import sys
from tools.config_loader import get_config_loader 
from tools.rerun import ControlMode, set_joints, joint_limits, normalize_to_radians, set_joints_radians, radians_to_normalized
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower
from inverse_kinematics.ik import RobotKinematics
import numpy as np
import rerun as rr
import time
from scipy.spatial.transform import Rotation as R
from controller.xbox import update_pose, log_pose_to_rerun, joystick
import pinocchio as pin
import pygame

# Load configuration
config_loader = get_config_loader()
follower_config = config_loader.get_follower_config()

if not follower_config:
    print("Error: Follower arm must be configured in config.yaml")
    sys.exit(1)

robot_config = SO101FollowerConfig(
    port=follower_config.port,
    id=follower_config.id,
)

robot = SO101Follower(robot_config)
robot.connect()

def get_action():
    # Get action from leader arm
    action = robot.get_observation()
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


q_sample = get_action()
ik = RobotKinematics()
base_target_matrix = ik.fk(q_sample, frame="gripper_link")

# Initialize position and orientation from the existing base_target_matrix
position = base_target_matrix[:3, 3]  # Extract position from matrix
orientation = R.from_matrix(base_target_matrix[:3, :3])  # Extract orientation from matrix

# Safety threshold for joint angle changes (in radians)
SAFETY_THRESHOLD = 0.5  # Adjust this value based on your robot's requirements

while True:
    try:
        pygame.event.pump()
        lx, ly = joystick.get_axis(0), joystick.get_axis(1)
        rx, ry = joystick.get_axis(2), joystick.get_axis(3)
        gripper_axis = joystick.get_axis(4)  # Get gripper control from axis 4

        def dz(x, t=0.1): return x if abs(x) > t else 0
        lx, ly, rx, ry = dz(lx), dz(ly), dz(rx), dz(ry)

        # Debug: print joystick values
        print(f"Raw: L({joystick.get_axis(0):.3f}, {joystick.get_axis(1):.3f}) R({joystick.get_axis(2):.3f}, {joystick.get_axis(3):.3f}) G({gripper_axis:.3f})")
        print(f"Deadzone: L({lx:.3f}, {ly:.3f}) R({rx:.3f}, {ry:.3f})")

        # Update pose using new quaternion-based approach
        position, orientation = update_pose(position, orientation, lx, ly, rx, ry)
        log_pose_to_rerun(position, orientation)

        # Convert position and orientation to transformation matrix for IK
        base_target_matrix = np.eye(4)
        base_target_matrix[:3, :3] = orientation.as_matrix()
        base_target_matrix[:3, 3] = position

        pos = base_target_matrix[:3, 3]

        colors = np.array([[255, 0, 0]])

        # Visualize end-effector position
        rr.log(
            "my_points",
            rr.Points3D(pos, colors=colors, radii=0.05)
        )

        q = ik.ik(q_sample, base_target_matrix, frame="gripper_link")
        
        # Safety check: compare q_sample and q
        if q is not None and q_sample is not None:
            joint_diff = np.abs(q - q_sample)
            max_diff = np.max(joint_diff)
            
            if max_diff > SAFETY_THRESHOLD:
                print(f"SAFETY WARNING: Large joint angle change detected!")
                print(f"Maximum change: {max_diff:.4f} radians (threshold: {SAFETY_THRESHOLD})")
                print(f"Joint differences: {joint_diff}")
                print("Shutting down for safety...")
                break
        
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
        
        # Convert radian_angles to action and normalize radians
        action = {}
        for motor, val in radian_angles.items():
            action[f"{motor}.pos"] = radians_to_normalized(val, motor)
        
        # Map gripper axis to gripper position (0-100 range)
        # gripper_axis ranges from -1 to 1, map to 0-100
        gripper_pos = int((gripper_axis + 1) * 50)  # Convert -1 to 1 range to 0 to 100
        action["gripper.pos"] = gripper_pos

        
        robot.send_action(action)
        q_sample = q
        time.sleep(0.1)
    except KeyboardInterrupt:
        print("Shutting down teleop...")
        break