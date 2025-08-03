import pygame
import numpy as np
import rerun as rr
from scipy.spatial.transform import Rotation as R

# Initialize pygame
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Initialize position and orientation
position = np.array([0.0, 0.0, 0.0])  # x, y, z
orientation = R.from_quat([0, 0, 0, 1])  # Identity quaternion

translation_speed = 0.01  # Units per frame
rotation_speed = 1.0  # Degrees per frame

def update_pose(position, orientation, left_x, left_y, right_x, right_y):
    # Ship-like controls:
    # Left stick: forward/backward (Y) and left/right (X) movement
    # Right stick: pitch (X) and yaw (Y) rotation
    
    # Translation in world frame
    # Forward/backward movement (Z-axis)
    forward_move = left_y * translation_speed
    # Left/right movement (X-axis)
    side_move = left_x * translation_speed
    
    # Update position
    new_position = position + np.array([side_move, 0.0, -forward_move])
    
    # Rotation controls - swapped axis mapping
    pitch_rad = np.radians(right_x * rotation_speed)  # Nose up/down (X-axis rotation)
    yaw_rad = np.radians(-right_y * rotation_speed)   # Turn left/right (Y-axis rotation, flipped direction)
    
    # Create rotation deltas
    pitch_rotation = R.from_rotvec([pitch_rad, 0, 0])
    yaw_rotation = R.from_rotvec([0, yaw_rad, 0])
    
    # Apply rotations to current orientation
    new_orientation = orientation * pitch_rotation * yaw_rotation
    
    return new_position, new_orientation

def log_pose_to_rerun(position, orientation):
    # Get forward direction from orientation
    forward_dir = orientation.apply([0, 0, -1])  # Forward is negative Z
    forward_point = position + forward_dir * 0.3  # 30cm forward
    
    rr.log("pose/position", rr.Points3D(
        positions=[position],
        colors=[[0, 255, 0]],  # Green for position
        radii=[0.02]
    ))
    
    rr.log("pose/forward", rr.Arrows3D(
        origins=[position],
        vectors=[forward_dir * 0.3],
        colors=[[255, 0, 0]],  # Red for forward direction
    ))

if __name__ == "__main__":
    try:
        while True:
            pygame.event.pump()
            lx, ly = joystick.get_axis(0), joystick.get_axis(1)
            rx, ry = joystick.get_axis(2), joystick.get_axis(3)

            def dz(x, t=0.1): return x if abs(x) > t else 0
            lx, ly, rx, ry = dz(lx), dz(ly), dz(rx), dz(ry)

            # Update pose
            position, orientation = update_pose(position, orientation, lx, ly, rx, ry)
            
            # Print current state
            euler_angles = orientation.as_euler('xyz', degrees=True)
            print(f"Pos: ({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f}) "
                  f"Rot: ({euler_angles[0]:.1f}°, {euler_angles[1]:.1f}°, {euler_angles[2]:.1f}°)")

            log_pose_to_rerun(position, orientation)

            pygame.time.wait(50)

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        pygame.quit()
