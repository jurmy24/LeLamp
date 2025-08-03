import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.config_loader import get_config_loader 
from lerobot.teleoperators.lelamp_leader import LeLampLeaderConfig, LeLampLeader
from tools.rerun import ControlMode, set_joints, set_led_intensity, normalize_to_radians, draw_transformation_matrix

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

target_pos = None

while True:
    try:
        # 1.
        # Get action from teleop device
        # Returns {"joint_name.pos": joint_value in normalized range -100 to +100, ...}
        action = teleop_device.get_action()

        # 2.
        # Calculate joint angles in degrees
        # joint_degrees = [degree for joint_name, joint_value in action.items() if joint_name.endswith(".pos")]
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

        # 3. 
        # Get the end-effector position
        # Forward kinematics to get the end-effector position
        world_frame = kinematics.forward_kinematics(joint_degrees)
        rotation_matrix = world_frame[:3, :3]
        translation_vector = world_frame[:3, 3]

        # 4.
        # Visualize the rotation and translation in Rerun
        draw_transformation_matrix(world_frame, name="end_effector")

        # 4. 
        # Teleop in rerun
        action_dict = {}

        for joint_name, joint_value in action.items():
            if joint_name.endswith(".pos"):
                joint_name = joint_name[:-4]
                action_dict[joint_name] = normalize_to_radians(joint_value, joint_name)

            elif joint_name.endswith(".intensity"):
                joint_name = joint_name[:-10]
                set_led_intensity(joint_value, position=[translation_vector])
                continue  # Skip intensity values

            if joint_name == "shoulder_pan":
                action_dict[joint_name] = - action_dict[joint_name]  # Invert shoulder pan for correct orientation

        set_joints(action_dict, ControlMode.RADIANS)
    except KeyboardInterrupt:
        print("Shutting down teleop...")
        break