#!/usr/bin/env python
# import rospy
import numpy as np
# import tf.transformations
import ros_compatibility as roscomp
from ros_compatibility.node import CompatibleNode
from rospy import Subscriber
from carla_msgs.msg import CarlaSpeedometer   # , CarlaWorldInfo
# from std_msgs.msg import String
from std_msgs.msg import Float32, Float32MultiArray
from std_msgs.msg import Bool
from perception.msg import MinDistance
import time


class CollisionCheck(CompatibleNode):
    """
    This is currently a test node. In the future this node will be
    responsible for detecting collisions and reporting them.
    """

    def __init__(self):
        super(CollisionCheck, self).__init__('CollisionCheck')
        self.role_name = self.get_param("role_name", "hero")
        self.control_loop_rate = self.get_param("control_loop_rate", 1)
        # self.current_speed = 50 / 3.6  # m/ss
        # TODO: Add Subscriber for Speed and Obstacles
        self.loginfo("CollisionCheck started")

        # self.obstacle_sub: Subscriber = self.new_subscription(
        # )
        # Subscriber for current speed
        self.velocity_sub: Subscriber = self.new_subscription(
            CarlaSpeedometer,
            f"/carla/{self.role_name}/Speed",
            self.__get_current_velocity,
            qos_profile=1)
        # Subscriber for lidar distance
        # TODO: Change to real lidar distance
        self.lidar_dist = self.new_subscription(
            MinDistance,
            f"/paf/{self.role_name}/Center/min_distance",
            self.calculate_obstacle_speed,
            qos_profile=1)
        # Publisher for emergency stop
        self.emergency_pub = self.new_publisher(
            Bool,
            f"/paf/{self.role_name}/emergency",
            qos_profile=1)
        # Publisher for distance to collision
        self.collision_pub = self.new_publisher(
            Float32MultiArray,
            f"/paf/{self.role_name}/collision",
            qos_profile=1)
        # Approx speed publisher for ACC
        self.speed_publisher = self.new_publisher(
            Float32,
            f"/paf/{self.role_name}/cc_speed",
            qos_profile=1)
        # Variables to save vehicle data
        self.__current_velocity: float = None
        self.__object_last_position: tuple = None

    def calculate_obstacle_speed(self, new_dist: MinDistance):
        """Caluclate the speed of the obstacle in front of the ego vehicle
            based on the distance between to timestamps

        Args:
            new_position (MinDistance): new position received from the lidar
        """
        # Check if current speed from vehicle is not None
        if self.__current_velocity is None:
            return
        # Check if this is the first time the callback is called
        if self.__object_last_position is None and \
                np.isinf(new_dist.distance) is not True:
            self.__object_last_position = (time.time(),
                                           new_dist.distance)
            return

        # If distance is np.inf no car is in front
        if np.isinf(new_dist.distance):
            self.__object_last_position = None
            return
        # Check if too much time has passed since last position update
        if self.__object_last_position[0] + \
                0.5 < time.time():
            self.__object_last_position = (time.time(),
                                           new_dist.distance)
            return
        # Calculate time since last position update
        current_time = time.time()
        time_difference = current_time-self.__object_last_position[0]

        # Calculate distance (in m)
        distance = new_dist.distance - self.__object_last_position[1]

        # Speed is distance/time (m/s)
        relative_speed = distance/time_difference
        speed = self.__current_velocity + relative_speed
        # Publish speed to ACC for permanent distance check
        self.speed_publisher.publish(Float32(data=speed))
        # Check for crash
        self.check_crash((new_dist.distance, speed))
        self.__object_last_position = (current_time, new_dist.distance)

    def __get_current_velocity(self, data: CarlaSpeedometer,):
        """Saves current velocity of the ego vehicle

        Args:
            data (CarlaSpeedometer): Message from carla with current speed
        """
        self.__current_velocity = float(data.speed)

    def time_to_collision(self, obstacle_speed, distance):
        """calculates the time to collision with the obstacle in front

        Args:
            obstacle_speed (float): Speed from obstacle in front
            distance (float): Distance to obstacle in front

        Returns:
            float: Time until collision with obstacle in front
        """
        if (self.__current_velocity - obstacle_speed) == 0:
            return -1
        return distance / (self.__current_velocity - obstacle_speed)

    def meters_to_collision(self, obstacle_speed, distance):
        """Calculates the meters until collision with the obstacle in front

        Args:
            obstacle_speed (float): speed from obstacle in front
            distance (float): distance from obstacle in front

        Returns:
            float: distance (in meters) until collision with obstacle in front
        """
        return self.time_to_collision(obstacle_speed, distance) * \
            self.__current_velocity

    @staticmethod
    def calculate_rule_of_thumb(emergency, speed):
        """Calculates the rule of thumb as approximation
        for the braking distance

        Args:
            emergency (bool): if emergency brake is initiated

        Returns:
            float: distance calculated with rule of thumb
        """
        reaction_distance = speed
        braking_distance = (speed * 0.36)**2
        if emergency:
            return reaction_distance + braking_distance / 2
        else:
            return reaction_distance + braking_distance

    def check_crash(self, obstacle):
        """ Checks if and when the ego vehicle will crash
            with the obstacle in front

        Args:
            obstacle (tuple): tuple with distance and
                                speed from obstacle in front
        """
        distance, obstacle_speed = obstacle

        collision_time = self.time_to_collision(obstacle_speed, distance)
        # collision_meter = self.meters_to_collision(obstacle_speed, distance)
        # safe_distance2 = self.calculate_rule_of_thumb(False)
        emergency_distance2 = self.calculate_rule_of_thumb(
            True, self.__current_velocity)
        if collision_time > 0:
            if distance < emergency_distance2:
                # Initiate emergency brake
                self.emergency_pub.publish(True)
                return
            # When no emergency brake is needed publish collision object
            data = Float32MultiArray(data=[distance, obstacle_speed])
            self.collision_pub.publish(data)
        else:
            # If no collision is ahead publish np.Inf
            data = Float32MultiArray(data=[np.Inf, obstacle_speed])
            self.collision_pub.publish(data)

    def run(self):
        """
        Control loop
        :return:
        """
        self.spin()


if __name__ == "__main__":
    """
    main function starts the CollisionCheck node
    :param args:
    """
    roscomp.init('CollisionCheck')

    try:
        node = CollisionCheck()
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        roscomp.shutdown()
