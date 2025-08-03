import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.config_loader import get_config_loader 
from lerobot.teleoperators.lelamp_leader import LeLampLeaderConfig, LeLampLeader
from lerobot.robots.lelamp_follower import LeLampFollowerConfig, LeLampFollower
from tools.rerun import ControlMode, set_joints, set_led_intensity, normalize_to_radians, radians_to_normalized
from opencv.aruco_detector import ArucoDetector

from lerobot.model.kinematics import RobotKinematics

import numpy as np
import rerun as rr

# Load configuration
config_loader = get_config_loader()
leader_config = config_loader.get_leader_config()
follower_config = config_loader.get_follower_config()

if not leader_config:
    print("Error: Leader arm must be configured in config.yaml")
    sys.exit(1)

teleop_config = LeLampLeaderConfig(
    port=leader_config.port,
    id=leader_config.id,
)

robot_config = LeLampFollowerConfig(
    port=follower_config.port,
    id=follower_config.id,
)

teleop_device = LeLampLeader(teleop_config)
robot_device = LeLampFollower(robot_config)
teleop_device.connect(calibrate=False)
robot_device.connect(calibrate=False)

# Set up the robot kinematics
kinematics = RobotKinematics(urdf_path="/Users/binhpham/workspace/le_lamp/models")

# Set up aruco detector
aruco_detector = ArucoDetector()

target_pos = np.array([0.0, 0.0, 0.0])  # Default target position

# Safety measure variables
previous_target_action = None
MAX_ACTION_DIFF_THRESHOLD = 2  # Maximum allowed difference in radians between consecutive actions
safety_enabled = True
detected_marker = False

while True:
    try:
        action = robot_device.get_observation()

        action_dict = {}

        # Calculate joint angles in degrees
        joint_degrees = []
        for joint_name, joint_value in action.items():
            if joint_name.endswith(".intensity"):
                continue

            if joint_name.endswith(".pos"):
                joint_name = joint_name[:-4]

            if joint_name == "shoulder_pan":
                joint_value = - joint_value

            degree = normalize_to_radians(joint_value, joint_name)

            # convert radians to degrees for visualization
            degree = np.rad2deg(degree)
            joint_degrees.append(degree)

        joint_degrees.append(0)  # Add a dummy value for the end effector

        # Forward kinematics to get the end-effector position
        world_frame = kinematics.forward_kinematics(joint_degrees)
        pos = world_frame[:3, 3]
        # target_pos = pos.copy()  # Default target position is the end-effector position

        poses = aruco_detector.get_pos()



        # Check for marker 2
        id = 6
        if id in poses:
            
            marker_pos = poses[id][:3, 3]
            marker_pos = - marker_pos + pos  # Adjust marker position by end-effector position
            print(f"Marker 6 position: ({marker_pos[0]:.3f}, {marker_pos[1]:.3f}, {marker_pos[2]:.3f})")

            # Visualize end-effector marker_pos
            marker_color = np.array([[0, 255, 0, 255]])
            target_color = np.array([[255, 0, 0, 255]])
            target_pos = np.array([marker_pos + np.array([0, 0, 0.05])])  # Slightly above the marker
            marker_pos = np.array([marker_pos])

            # print target position
            # print(f"Target position: ({target_pos[0][0]:.3f}, {target_pos[0][1]:.3f}, {target_pos[0][2]:.3f})")

            rr.log(
                "end_effector_marker",
                rr.Points3D(marker_pos, colors=marker_color, radii=0.001)  # Scale radius by intensity
            )

            rr.log(
                "target_position",
                rr.Points3D(target_pos, colors=target_color, radii=0.01)  # Scale radius by intensity
            )

            detected_marker = True

        target_frame = world_frame
        target_frame[:3, 3] = target_pos

        target_degrees = kinematics.inverse_kinematics(
            joint_degrees,
            target_frame
        )

        
        # print(f"Target joint angles: {target_degrees}")

        # turn target_degrees into radians
        target_degrees_rad = np.deg2rad(target_degrees[:len(kinematics.joint_names)])

        target_action = {}
        # Put in dictionary for
        for degree_rad in target_degrees_rad:
            joint_name = kinematics.joint_names[len(target_action)]
            target_action[joint_name] = degree_rad
            
        # Safety check: compare with previous target action
        if previous_target_action is not None and safety_enabled:
            max_diff = 0.0
            for joint_name in target_action:
                if joint_name in previous_target_action:
                    diff = abs(target_action[joint_name] - previous_target_action[joint_name])
                    max_diff = max(max_diff, diff)
            
            if max_diff > MAX_ACTION_DIFF_THRESHOLD:
                print(f"WARNING: Large action difference detected ({max_diff:.3f} rad > {MAX_ACTION_DIFF_THRESHOLD} rad)")
                print("Safety measure activated - turning off system")
                safety_enabled = False
                # Send zero action to stop the robot
                zero_action = {joint_name: 0.0 for joint_name in target_action}
                zero_action['led.intensity'] = 0
                robot_device.send_action(zero_action)
                continue
        
        previous_target_action = target_action.copy()
        
        print(f"Target action: {target_action}")

        #Set joints in rerun
        # for joint_name, joint_value in action.items():
        #     if joint_name.endswith(".pos"):
        #         joint_name = joint_name[:-4]
        #     elif joint_name.endswith(".intensity"):
        #         joint_name = joint_name[:-10]
        #         set_led_intensity(joint_value, position=pos)
        #         continue  # Skip intensity values

        #     action_dict[joint_name] = joint_value

        #     if joint_name == "shoulder_pan":
        #         action_dict[joint_name] = - joint_value


        set_joints(target_action, ControlMode.RADIANS)
        # Only execute if safety is enabled
        
        if safety_enabled:
            
            # remove gripper action if it exists
            if 'gripper' in target_action:
                del target_action['gripper']

            # Turn to normalized values
            target_action_norm = {f"{k}.pos": radians_to_normalized(v, k) for k, v in target_action.items()}


            target_action_norm['led.intensity'] = 0  # Set light intensity to 0%

            
            # print new target action
            print(f"Executing target action: {target_action_norm}")
            
            if detected_marker:
                print("Detected marker, sending action to robot.")
                robot_device.send_action(target_action_norm)
        else:
            print("System disabled due to safety measure. Press Ctrl+C to exit.")
    except KeyboardInterrupt:
        print("Shutting down teleop...")
        break