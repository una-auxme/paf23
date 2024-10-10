# Architecture

**Summary**: This documentation shows the current Acting Architecture.

- [Architecture](#architecture)
  - [Acting Architecture](#acting-architecture)
  - [Summary of Acting Components](#summary-of-acting-components)
    - [pure\_pursuit\_controller.py](#pure_pursuit_controllerpy)
    - [stanley\_controller.py](#stanley_controllerpy)
    - [velocity\_controller.py](#velocity_controllerpy)
    - [vehicle\_controller.py](#vehicle_controllerpy)
    - [helper\_functions.py](#helper_functionspy)
    - [MainFramePublisher.py](#mainframepublisherpy)

## Acting Architecture

![MISSING: Acting-ARCHITECTURE](../assets/acting/Architecture_Acting.png)

## Summary of Acting Components

### pure_pursuit_controller.py

- Inputs:
  - **trajectory**: Path
  - **current_pos**: PoseStamped
  - **Speed**: CarlaSpeedometer
  - **current_heading**: Float32
- Outputs:
  - **pure_pursuit_steer**: Float32
  - **pure_p_debug**: Debug

### stanley_controller.py

- Inputs:
  - **trajectory**: Path
  - **current_pos**: PoseStamped
  - **Speed**: CarlaSpeedometer
  - **current_heading**: Float32
- Outputs:
  - **stanley_steer**: Float32
  - **stanley_debug**: StanleyDebug

### velocity_controller.py

- Inputs:
  - **target_velocity**: Float32
  - **Speed**: CarlaSpeedometer
- Outputs:
  - **throttle**: Float32
  - **brake**: Float32

### vehicle_controller.py

- Inputs:
  - **emergency**: Bool
  - **curr_behavior**: String
  - **Speed**: CarlaSpeedometer
  - **throttle**: Float32
  - **brake**: Float32
  - **pure_pursuit_steer**: Float32
  - **stanley_steer**: Float32
- Outputs:
  - **vehicle_control_cmd**: [CarlaEgoVehicleControl](https://carla.readthedocs.io/en/0.9.8/ros_msgs/#CarlaEgoVehicleControlmsg)
  - **status**: Bool
  - **emergency**: Bool

### helper_functions.py

- **vectors_to_angle_abs(x1: float, y1: float, x2: float, y2: float) -> float**:\
Returns the angle (radians) between the two given vectors
- **vector_angle(x1: float, y1: float) -> float**:\
Returns the angle (radians) of a given vectors
- **vector_to_direction(x1, y1, x2, y2) -> float**:\
Returns the direction (angle to y-axis) of a vector  
- **quaternion_to_heading(x: float, y: float, z: float, w: float) -> float**:\
Translates quaternion to euler heading
- **heading_to_quaternion(heading: float) -> (float, float, float, float)**:\
Translates euler heading to quaternion
- **calc_path_yaw(path: Path, idx: int) -> float**:\
Calculates the path yaw
- **normalize_angle(angle: float) -> float**:\
Normalizes an angle to [-pi, pi]
- **calc_egocar_yaw(pose: PoseStamped) -> float**:\
Calculates the yaw of the ego vehicle
- **points_to_vector(p_1: Tuple[float, float], p_2: Tuple[float, float]) -> Tuple[float, float]**:\
Create the vector starting at p1 and ending at p2
- **vector_len(vec: Tuple[float, float]) -> float**:\
Compute the given vector's length
- **add_vector(v_1: Tuple[float, float], v_2: Tuple[float, float]) -> Tuple[float, float]**:\
Add the two given vectors
- **rotate_vector(vector: Tuple[float, float], angle_rad: float) -> Tuple[float, float]**:\
Rotate the given vector by an angle
- **linear_interpolation(start: Tuple[float, float], end: Tuple[float, float], interval_m: float) -> List[Tuple[float, float]]**:\
Interpolate linearly between start and end, with a minimal distance of interval_m between points.
- **_clean_route_duplicates(route: List[Tuple[float, float]], min_dist: float) -> List[Tuple[float, float]]**:\
Remove duplicates in the given List of tuples, if the distance between them is less than min_dist.
- **interpolate_route(orig_route: List[Tuple[float, float]], interval_m=0.5)**:\
Interpolate the given route with points inbetween,holding the specified distance interval threshold.

### MainFramePublisher.py

- Inputs:
  - **current_pos**: PoseStampled
  - **current_heading**: Float32
- Outputs:
  - **transform**: broadcasts heroframe-transform via TransformBroadcaster
- This node handles the translation from the static main frame to the moving hero frame. The hero frame always moves and rotates as the ego vehicle does. The hero frame is used by sensors like the lidar. Rviz also uses the hero frame. The main frame is used for planning
- rotation = - **current_heading**
- position x = cos(rotation) \* **current_pos**.x + sin(rotation) \* **current_pos**.y
- position y = sin(rotation) \* **current_pos**.x + cos(rotation) \* **current_pos**.y
- position z = - **current_pos**.z
- rot_quat = rot as quaternion
- **transform** = position x/y/z, rot_quat, Timestamp(now), “global”, “hero”
