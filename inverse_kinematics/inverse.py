"""
This script is testthe forward and inverse kinematics of the robot.
It uses the leader arm to get the joint angles and then visualizes the end-effector position.
It then uses the inverse kinematics to get the joint angles that would result in the end-effector being at the desired position.
"""

from .ik import RobotKinematics
import numpy as np
import rerun as rr
from pathlib import Path 
import sys
import time
sys.path.append(str(Path(__file__).parent.parent))

from tools.config_loader import get_config_loader
from tools.rerun import ControlMode, set_joints, joint_limits, normalize_to_radians, set_joints_radians
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader

# Set up leader arm
# Load robot configuration
config_loader = get_config_loader()
leader_config = config_loader.get_leader_config()

if not leader_config:
    print("Error: Leader arm must be configured in config.yaml")
    sys.exit(1)

teleop_config = SO101LeaderConfig(
    port=leader_config.port,
    id=leader_config.id,
)

teleop_device = SO101Leader(teleop_config)
teleop_device.connect()

# Initialize robot kinematics
ik = RobotKinematics()

def get_action():
    # Get action from leader arm
    action = teleop_device.get_action()
    action_dict = {}

    # Annotate normalized joint angles and modify gripper and shoulder_pan
    for joint_name, joint_value in action.items():
        name = joint_name[0:-4]
        action_dict[name] = joint_value
        if name == "gripper":
            action_dict[name] = 100 - joint_value
        elif name == "shoulder_pan":
            action_dict[name] = - joint_value

    # Convert normalized joint angles to radian angles
    radian_angles = {}
    for joint_key, normalized_value in action_dict.items():
        if joint_key in joint_limits:
            radian_angles[joint_key] = normalize_to_radians(normalized_value, joint_key)

    q_sample = [radian_angles["shoulder_pan"], radian_angles["shoulder_lift"], radian_angles["elbow_flex"], radian_angles["wrist_flex"], radian_angles["wrist_roll"], radian_angles["gripper"]]
    q_sample = np.array(q_sample)

    return q_sample

# Get initial position of arm and initial joint angles
q_sample = get_action()
T = ik.fk(q_sample, frame="gripper_link")

if __name__ == "__main__":
    while True:
        T[2, 3] += 0.001
        pos = T[:3, 3]

        # flip x and y
        pos = np.array([pos[0], -pos[1], pos[2]])

        colors = np.array([[255, 0, 0]])

        # Visualize end-effector position
        rr.log(
            "my_points",
            rr.Points3D(pos, colors=colors, radii=0.05)
        )

        q = ik.ik(q_sample, T, frame="gripper_link")
        radian_angles = {
            "shoulder_pan": q[0],
            "shoulder_lift": q[1],
            "elbow_flex": q[2],
            "wrist_flex": q[3],
            "wrist_roll": q[4],
            "gripper": q[5],
        }

        set_joints_radians(radian_angles)
        q_sample = q
        time.sleep(0.1)