#!/usr/bin/env python

import numpy as np
import ros_compatibility as roscomp
from ros_compatibility.node import CompatibleNode
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, UInt32
from sensor_msgs.msg import NavSatFix, Imu
from tf.transformations import euler_from_quaternion
from carla_msgs.msg import CarlaSpeedometer
import math

'''
This class implements a Kalman filter for a 3D object tracked in 3D space.
It implements the data of the IMU and the GPS Sensors.
The IMU Sensor provides the acceleration
and the GPS Sensor provides the position.
The Carla Speedometer provides the current Speed in the headed direction.

The Noise for the GPS Sensor is defined as:
    "noise_alt_stddev": 0.000005,
    "noise_lat_stddev": 0.000005,
    "noise_lon_stddev": 0.000005
The Noise for the IMU Sensor is defined as:
    "noise_accel_stddev_x": 0.001,
    "noise_accel_stddev_y": 0.001,
    "noise_accel_stddev_z": 0.015,

The state vector X is defined as:
            [initial_x],
            [initial_y],
            [yaw],
            [v_hy] in direction of heading hy,
            [a_hy] in direction of v_hy (heading hy),
            [omega_z],
The state transition matrix F is defined as:
    A = I
    I: Identity Matrix
The measurement matrix H is defined as:
    H = [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1]
The process covariance matrix Q is defined as:
    Q = np.diag([0.005, 0.005, 0.001, 0.0001]
'''


class KalmanFilter(CompatibleNode):
    """
    This class implements a Kalman filter for a 3D object tracked in 3D space.
    """
    def __init__(self):
        """
        Constructor / Setup
        :return:
        """

        super(KalmanFilter, self).__init__('kalman_filter_node')

        self.loginfo('KalmanFilter node started')
        # basic info
        self.role_name = self.get_param("role_name", "hero")
        self.control_loop_rate = self.get_param("control_loop_rate", "0.001")
        self.publish_seq = UInt32(0)
        self.frame_id = "map"

        self.dt = self.control_loop_rate

        # Initialize the state vector X
        '''
        [
            [initial_x],
            [initial_y],
            [yaw],
            [v_hy] in direction of heading hy,
            [a_hy] in direction of v_hy (heading hy),
            [omega_z],
        ]
        '''
        self.x0 = np.zeros((6, 1))

        # Define initial state covariance matrix
        self.P0 = np.eye(6)

        # Define state transition matrix
        # [x, y, yaw, v_hy, a_hy, omega_z]
        # [             ...              ]
        self.A = np.array([[1, 0, 0, self.dt, 0, 0],
                           [0, 1, 0, 0, self.dt, 0],
                           [0, 0, 1, 0, 0, self.dt],
                           [0, 0, 0, 1, 0, 0],
                           [0, 0, 0, 0, 1, 0],
                           [0, 0, 0, 0, 0, 1]])

        # Define measurement matrix
        '''
        1. GPS: x, y
        2. IMU: yaw, omega_z
        -> 4 measurements for a state vector of 6
        (v is not in the measurement here because its provided by Carla)
        '''
        self.H = np.array([[1, 0, 0, 0, 0, 0],
                           [0, 1, 0, 0, 0, 0],
                           [0, 0, 1, 0, 0, 0],
                           [0, 0, 0, 0, 0, 1]])

        # Define process noise covariance matrix
        self.Q = np.diag([0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001])

        # Define measurement noise covariance matrix
        self.R = np.diag([0.005, 0.005, 0.001, 0.0001])

        # Define Measurement Variables
        self.z_gps = np.zeros((2, 1))  # GPS measurements (x, y)
        self.z_imu = np.zeros((2, 1))  # IMU measurements (yaw, omega_z)

        self.v = np.zeros((2, 1))  # Velocity measurements (v_x, v_y)

        self.x_old_est = np.copy(self.x0)  # old state vector
        self.P_old_est = np.copy(self.P0)  # old state covariance matrix
        self.x_est = np.zeros((6, 1))  # estimated state vector
        self.P_est = np.zeros((6, 6))  # estiamted state covariance matrix
        self.x_pred = np.zeros((6, 1))  # Predicted state vector
        self.P_pred = np.zeros((6, 6))  # Predicted state covariance matrix

        self.K = np.zeros((6, 4))  # Kalman gain

        self.latitude = 0  # latitude of the current position

        '''
        # Define control input vector
        u = np.array([0, 0, -g, 0, 0, 0])

        # Define control input matrix
        B = np.array([[0, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                    [0, 0, dt],
                    [0, dt, 0],
                    [dt, 0, 0]])
        '''

        # Subscriber
        # Initialize the subscriber for the IMU Data
        self.imu_subscriber = self.new_subscription(
            Imu,
            "/carla/" + self.role_name + "/Ideal_IMU",
            self.update_imu_data,
            qos_profile=1)
        # Initialize the subscriber for the GPS Data
        self.gps_subscriber = self.new_subscription(
            NavSatFix,
            "/carla/" + self.role_name + "/GPS",
            self.update_gps_data,
            qos_profile=1)
        # Initialize the subscriber for the current_pos in XYZ
        self.current_pos_subscriber = self.new_subscription(
            PoseStamped,
            "/paf/" + self.role_name + "/current_pos",
            self.update_current_pos,
            qos_profile=1)
        # Initialize the subscriber for the velocity
        self.velocity_subscriber = self.new_subscription(
            CarlaSpeedometer,
            "/carla/" + self.role_name + "/Speed",
            self.update_velocity,
            qos_profile=1)

        # Publisher
        # Initialize the publisher for the kalman-position
        self.kalman_position_publisher = self.new_publisher(
            PoseStamped,
            "/paf/" + self.role_name + "/kalman_pos",
            qos_profile=1)
        self.kalman_heading_publisher = self.new_publisher(
            Float32,
            "/paf/" + self.role_name + "/kalman_heading",
            qos_profile=1)

    def run(self):
        """
        Run the Kalman Filter
        """
        def loop():
            """
            Loop for the Kalman Filter
            """
            self.predict()
            self.update()

            # Publish the kalman-data:
            self.publish_kalman_heading()
            self.publish_kalman_location()

        # roscomp.spin(loop, self.control_loop_rate)
        self.new_timer(self.control_loop_rate, loop)
        self.spin()

    def predict(self):
        """
        Predict the next state
        """
        # Update the old state and covariance matrix
        self.x_old_est[:, :] = np.copy(self.x_est[:, :])
        self.P_old_est[:, :] = np.copy(self.P_est[:, :])

        # Predict the next state and covariance matrix
        self.x_pred = self.A @ self.x_est[:]  # + B @ v[:, k-1] + u
        self.P_pred = self.A @ self.P_est[:, :] @ self.A.T + self.Q

    def update(self):
        """
        Update the state
        """
        z = np.concatenate((self.z_gps[:], self.z_imu[:]))  # Measurementvector
        y = z - self.H @ self.x_pred  # Measurement residual
        S = self.H @ self.P_pred @ self.H.T + self.R  # Residual covariance
        self.K[:, :] = self.P_pred @ self.H.T @ np.linalg.inv(S)  # Kalman gain
        self.x_est[:] = self.x_pred + self.K[:, :] @ y  # State estimate
        # State covariance estimate
        self.P_est[:, :] = (np.eye(6) - self.K[:, :] @ self.H) @ self.P_pred

    def publish_kalman_heading(self):
        """
        Publish the kalman heading
        """
        # Initialize the kalman-heading
        kalman_heading = Float32()

        # Fill the kalman-heading
        kalman_heading.data = self.x_est[2]

        # Publish the kalman-heading
        self.kalman_heading_publisher.publish(kalman_heading)

    def publish_kalman_location(self):
        """
        Publish the kalman location
        """
        # Initialize the kalman-position
        kalman_position = PoseStamped()

        # Fill the kalman-position
        kalman_position.header.frame_id = self.frame_id
        kalman_position.header.stamp = roscomp.Time.now()
        kalman_position.header.seq = self.publish_seq
        self.publish_seq.data += 1

        kalman_position.pose.position.x = self.x_est[0]
        kalman_position.pose.position.y = self.x_est[1]
        kalman_position.pose.position.z = self.latitude
        kalman_position.pose.orientation.x = 0
        kalman_position.pose.orientation.y = 0
        kalman_position.pose.orientation.z = 1
        kalman_position.pose.orientation.w = 0

        # Publish the kalman-position
        self.kalman_position_publisher.publish(kalman_position)

    def update_imu_data(self, imu_data):
        """
        Update the IMU Data
        """
        orientation_x = imu_data.orientation.x
        orientation_y = imu_data.orientation.y
        orientation_z = imu_data.orientation.z
        orientation_w = imu_data.orientation.w

        # Calculate the heading based on the orientation given by the IMU
        data_orientation_q = [orientation_x,
                              orientation_y,
                              orientation_z,
                              orientation_w]

        # Implementation by paf22 in Position_Publisher_Node.py
        # TODO: Why were they using roll and pitch instead of yaw?
        # Even though they are basically deriving the yaw that way?
        roll, pitch, yaw = euler_from_quaternion(data_orientation_q)
        raw_heading = math.atan2(roll, pitch)

        # transform raw_heading so that:
        # ---------------------------------------------------------------
        # | 0 = x-axis | pi/2 = y-axis | pi = -x-axis | -pi/2 = -y-axis |
        # ---------------------------------------------------------------
        heading = (raw_heading - (math.pi / 2)) % (2 * math.pi) - math.pi

        # update IMU Measurements:
        self.z_imu[0] = heading
        self.z_imu[1] = imu_data.angular_velocity.z
        if imu_data.orientation_covariance[8] != 0:
            # [8] because we want the diag z element of the covariance matrix
            self.R[2, 2] = imu_data.orientation_covariance[8]
        if imu_data.angular_velocity_covariance[8] != 0:
            # [8] because we want the diag z element of the covariance matrix
            self.R[3, 3] = imu_data.angular_velocity_covariance[8]

    def update_gps_data(self, gps_data):
        """
        Update the GPS Data
        Currently only used for covariance matrix
        """
        # look up if covariance type is not 0 (0 = COVARANCE_TYPE_UNKNOWN)
        # (1 = approximated, 2 = diagonal known or 3 = known)
        # if it is not 0 -> update the covariance matrix
        if gps_data.position_covariance_type != 0:
            # [0] because we want the diag lat element of the covariance matrix
            self.R[0, 0] = gps_data.pose.covariance[0]
            # [5] because we want the diag lon element of the covariance matrix
            self.R[1, 1] = gps_data.pose.covariance[5]
        pass

    def update_current_pos(self, current_pos):
        """
        Update the current position
        """
        # update GPS Measurements:
        self.z_gps[0] = current_pos.pose.position.x
        self.z_gps[1] = current_pos.pose.position.y

        self.latitude = current_pos.pose.position.z

    def update_velocity(self, velocity):
        """
        Update the velocity using the yaw angle in the predicted state x1
        x1[2] = yaw
        """
        self.v[0] = velocity.speed * math.cos(self.x_est[2])
        self.v[1] = velocity.speed * math.sin(self.x_est[2])


def main(args=None):
    """
    Main function starts the node
    :param args:
    """
    roscomp.init('kalman_filter_node', args=args)

    try:
        node = KalmanFilter()
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        roscomp.shutdown()


if __name__ == '__main__':
    main()
