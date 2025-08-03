import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.config_loader import get_config_loader 
from lerobot.teleoperators.lelamp_leader import LeLampLeaderConfig, LeLampLeader
from tools.rerun import ControlMode, set_joints, set_led_intensity, normalize_to_radians
from opencv.aruco_detector import ArucoDetector

from lerobot.model.kinematics import RobotKinematics

import numpy as np
import rerun as rr


# Load configuration
config_loader = get_config_loader()
leader_config = config_loader.get_leader_config()

if not leader_config:
    print("Error: Leader arm must be configured in config.yaml")
    sys.exit(1)

teleop_config = LeLampLeaderConfig(
    port=leader_config.port,
    id=leader_config.id,
)

teleop_device = LeLampLeader(teleop_config)
teleop_device.connect()

# Set up the robot kinematics
kinematics = RobotKinematics(urdf_path="/Users/binhpham/workspace/le_lamp/models")

# Set up aruco detector
aruco_detector = ArucoDetector()

target_pos = None

while True:
    try:
        action = teleop_device.get_action()
        action_dict = {}

        # Calculate joint angles in degrees
        joint_degrees = []
        for joint_name, joint_value in action.items():
            if joint_name.endswith(".intensity"):
                continue

            if joint_name.endswith(".pos"):
                joint_name = joint_name[:-4]

            degree = normalize_to_radians(joint_value, joint_name)

            # convert radians to degrees for visualization
            degree = np.rad2deg(degree)
            joint_degrees.append(degree)

        joint_degrees.append(0)  # Add a dummy value for the end effector

        # Forward kinematics to get the end-effector position
        world_frame = kinematics.forward_kinematics(joint_degrees)
        pos = world_frame[:3, 3]

        poses = aruco_detector.get_pos()

        target_pos = pos.copy()  # Default target position is the end-effector position

        # Check for marker 2
        if 6 in poses:
            marker_pos = poses[6][:3, 3]
            marker_pos = - marker_pos + pos  # Adjust marker position by end-effector position
            print(f"Marker 6 position: ({marker_pos[0]:.3f}, {marker_pos[1]:.3f}, {marker_pos[2]:.3f})")

            # Visualize end-effector marker_pos
            marker_color = np.array([[0, 255, 0, 255]])
            target_color = np.array([[255, 0, 0, 255]])
            target_pos = np.array([marker_pos + np.array([0, 0, 0.05])])  # Slightly above the marker
            marker_pos = np.array([marker_pos])

            # print target position
            print(f"Target position: ({target_pos[0][0]:.3f}, {target_pos[0][1]:.3f}, {target_pos[0][2]:.3f})")

            rr.log(
                "end_effector_marker",
                rr.Points3D(marker_pos, colors=marker_color, radii=0.001)  # Scale radius by intensity
            )

            rr.log(
                "target_position",
                rr.Points3D(target_pos, colors=target_color, radii=0.01)  # Scale radius by intensity
            )

        target_frame = world_frame
        target_frame[:3, 3] = target_pos if 'target_pos' in locals() else pos

        target_degrees = kinematics.inverse_kinematics(
            joint_degrees,
            target_frame
        )

        print(f"Target joint angles: {target_degrees}")

        # turn target_degrees into radians
        target_degrees_rad = np.deg2rad(target_degrees[:len(kinematics.joint_names)])

        target_action = {}
        # Put in dictionary for
        for degree_rad in target_degrees_rad:
            joint_name = kinematics.joint_names[len(target_action)]
            target_action[joint_name] = degree_rad
            
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
    except KeyboardInterrupt:
        print("Shutting down teleop...")
        break