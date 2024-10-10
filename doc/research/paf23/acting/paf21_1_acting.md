# Research: PAF21_1 Acting

**Summary:** This page contains the research into the action component of the PAF21_1 group.

- [Research: PAF21\_1 Acting](#research-paf21_1-acting)
  - [Inputs](#inputs)
  - [Curve Detection](#curve-detection)
  - [Speed Control](#speed-control)
  - [Steering Control](#steering-control)
    - [Straight Trajectories](#straight-trajectories)
    - [Detected Curves](#detected-curves)

## Inputs

- waypoints of the planned route
- general odometry of the vehicle

## Curve Detection

- Can detect curves on the planned trajectory
- Calculates the speed in which to drive the detected Curve
![Curve](../../assets/research_assets/curve_detection_paf21_1.png)

## Speed Control

- [CARLA Ackermann Control](https://carla.readthedocs.io/projects/ros-bridge/en/latest/carla_ackermann_control/)
- Speed is forwarded to the CARLA vehicle via Ackermann_message, which already includes a PID controller for safe driving/accelerating etc.
- no further controlling needed  -> speed can be passed as calculated

## Steering Control

### Straight Trajectories

- **Stanley Steering Controller**
  - Calculates steering angle from offset and heading error
  - includes PID controller
 ![Stanley Controller](../../assets/research_assets/stanley_paf21_1.png)

### Detected Curves

- **Naive Steering Controller** (close to pure pursuit)
  - uses Vehicle Position + Orientation + Waypoints
    - Calculate direction to drive to as vector
    - direction - orientation = Steering angle at each point in time
    - speed is calculated in Curve Detection and taken as is
