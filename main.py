import pygame
import numpy as np
import pinocchio as pin
import rerun as rr
from scipy.spatial.transform import Rotation as R
from inverse_kinematics.inverse import get_action, q_sample, T, ik, set_joints_radians
from controller.xbox import update_pose, log_pose_to_rerun, joystick

# Initialize position and orientation from the existing T matrix
position = T[:3, 3]  # Extract position from T matrix
orientation = R.from_matrix(T[:3, :3])  # Extract orientation from T matrix

# Safety threshold for joint angle changes (in radians)
SAFETY_THRESHOLD = 5  # Adjust this value based on your robot's requirements

try:
    while True:
        pygame.event.pump()
        lx, ly = joystick.get_axis(0), joystick.get_axis(1)
        rx, ry = joystick.get_axis(2), joystick.get_axis(3)

        def dz(x, t=0.1): return x if abs(x) > t else 0
        lx, ly, rx, ry = dz(lx), dz(ly), dz(rx), dz(ry)

        # Update pose using new quaternion-based approach
        position, orientation = update_pose(position, orientation, lx, ly, rx, ry)
        log_pose_to_rerun(position, orientation)

        # Convert position and orientation to transformation matrix for IK
        H = np.eye(4)
        H[:3, :3] = orientation.as_matrix()
        H[:3, 3] = position

        pos = H[:3, 3]

        # flip x and y
        pos = np.array([pos[0], -pos[1], pos[2]])
        print(pos)

        colors = np.array([[255, 0, 0]])

        # Visualize end-effector position
        rr.log(
            "my_points",
            rr.Points3D(pos, colors=colors, radii=0.05)
        )

        q = ik.ik(q_sample, H, frame="gripper_link")
        
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

        pygame.time.wait(50)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    pygame.quit()
