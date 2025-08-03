import rerun as rr  # NOTE: `rerun`, not `rerun-sdk`!
import numpy as np
import time
from pathlib import Path
from rerun import RotationAxisAngle
from enum import Enum

class ControlMode(Enum):
    RADIANS = "radians"
    NORMALIZED = "normalized"

# Initialize Rerun
rr.init("so101_simultaneous_demo", spawn=True)

# Load the URDF file
urdf_path = Path("models/so101.urdf")
rr.log_file_from_path(urdf_path, static=False)

rr.log("/", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

joint_limits = {
    "gripper": {
        "name": "so101/base_link/shoulder_pan/shoulder_link/shoulder_lift/upper_arm_link/elbow_flex/lower_arm_link/wrist_flex/wrist_link/wrist_roll/gripper_link/gripper",
        "lower": -1.74533,
        "upper": 0.174533,
        "axis": [0, 1, 0]
    },
    "wrist_roll": {
        "name": "so101/base_link/shoulder_pan/shoulder_link/shoulder_lift/upper_arm_link/elbow_flex/lower_arm_link/wrist_flex/wrist_link/wrist_roll",
        "lower": -2.74385,
        "upper": 2.84121,
        "axis": [0, 1, 0]
    },
    "wrist_flex": {
        "name": "so101/base_link/shoulder_pan/shoulder_link/shoulder_lift/upper_arm_link/elbow_flex/lower_arm_link/wrist_flex",
        "lower": -1.65806,
        "upper": 1.65806,
        "axis": [0, 0, 1]
    },
    "elbow_flex": {
        "name": "so101/base_link/shoulder_pan/shoulder_link/shoulder_lift/upper_arm_link/elbow_flex",
        "lower": -1.69,
        "upper": 1.69,
        "axis": [0, 0, 1]
    },
    "shoulder_lift": {
        "name": "so101/base_link/shoulder_pan/shoulder_link/shoulder_lift",
        "lower": -1.74533,
        "upper": 1.74533,
        "axis": [0, 1, 0]
    },
    "shoulder_pan": {
        "name": "so101/base_link/shoulder_pan",
        "lower": -1.91986,
        "upper": 1.91986,
        "axis": [0, 0, 1]
    }
}

def normalize_to_radians(normalized_value, joint_key):
    """Convert normalized value (-100 to 100) to radians"""
    if joint_key not in joint_limits:
        raise ValueError(f"Unknown joint: {joint_key}")
    
    # Clamp normalized value to valid range
    normalized_value = max(-100, min(100, normalized_value))
    
    joint_info = joint_limits[joint_key]
    lower = joint_info["lower"]
    upper = joint_info["upper"]
    
    # Convert from [-100, 100] to [lower, upper]
    normalized_ratio = (normalized_value + 100) / 200  # Convert to [0, 1]
    radian_value = lower + normalized_ratio * (upper - lower)
    
    return radian_value

def radians_to_normalized(radian_value, joint_key):
    """Convert radians to normalized value (-100 to 100)"""
    if joint_key not in joint_limits:
        raise ValueError(f"Unknown joint: {joint_key}")
    
    joint_info = joint_limits[joint_key]
    lower = joint_info["lower"]
    upper = joint_info["upper"]
    
    # Clamp radian value to valid range
    radian_value = max(lower, min(upper, radian_value))
    
    # Convert from [lower, upper] to [-100, 100]
    normalized_ratio = (radian_value - lower) / (upper - lower)  # Convert to [0, 1]
    normalized_value = -100 + normalized_ratio * 200  # Convert to [-100, 100]
    
    return normalized_value

def validate_radian_angles(joint_angles):
    """Validate that all radian angles are within joint limits"""
    validated_angles = {}
    for joint_key, angle in joint_angles.items():
        if joint_key in joint_limits:
            joint_info = joint_limits[joint_key]
            lower = joint_info["lower"]
            upper = joint_info["upper"]
            
            # Clamp to valid range
            clamped_angle = max(lower, min(upper, angle))
            if clamped_angle != angle:
                print(f"Warning: Joint '{joint_key}' angle {angle:.4f} clamped to {clamped_angle:.4f}")
            
            validated_angles[joint_key] = clamped_angle
        else:
            print(f"Warning: Unknown joint '{joint_key}' ignored")
    
    return validated_angles

def set_joints_radians(joint_angles):
    """Set joints using radian values (lower to upper limits)"""
    validated_angles = validate_radian_angles(joint_angles)
    
    for joint_key, angle in validated_angles.items():
        joint_info = joint_limits[joint_key]
        joint_name = joint_info["name"]
        joint_axis = joint_info["axis"]
        
        rotation = RotationAxisAngle(axis=joint_axis, angle=angle)
        rr.log(joint_name, rr.Transform3D(rotation=rotation))
    
    return validated_angles

def set_led_intensity(intensity, position=None):
    """Set LED intensity (0 to 100)"""

    # Make a point in rerun
    colors = np.array([[255, 0, 0, intensity]])
    if position is None:
        position = np.array([[0, 0, 1]])

    # Visualize end-effector position
    rr.log(
        "my_points ",
        rr.Points3D(position, colors=colors, radii=intensity / 255.0)  # Scale radius by intensity
    )

def set_joints_normalized(joint_values):
    """Set joints using normalized values (-100 to 100)"""
    # Convert normalized values to radians
    radian_angles = {}
    for joint_key, normalized_value in joint_values.items():
        if joint_key in joint_limits:
            radian_angles[joint_key] = normalize_to_radians(normalized_value, joint_key)
        else:
            print(f"Warning: Unknown joint '{joint_key}' ignored")
    
    # Set joints using radian values
    return set_joints_radians(radian_angles)

def set_joints(joint_values, mode=ControlMode.RADIANS):
    """Universal joint setter that handles both modes"""
    if mode == ControlMode.RADIANS:
        return set_joints_radians(joint_values)
    elif mode == ControlMode.NORMALIZED:
        return set_joints_normalized(joint_values)
    else:
        raise ValueError(f"Invalid control mode: {mode}")

def draw_transformation_matrix(matrix, name="transformation"):
    # Check shape
    if matrix.shape != (4, 4):
        raise ValueError("Transformation matrix must be 4x4")

    rotation_matrix = matrix[:3, :3]
    translation_vector = matrix[:3, 3]

    # 4.
    # Visualize the rotation and translation in Rerun
    x_vector = np.array([1, 0, 0])
    y_vector = np.array([0, 1, 0])
    z_vector = np.array([0, 0, 1])

    # Transform the vectors using the rotation matrix
    x_transformed = rotation_matrix @ x_vector
    y_transformed = rotation_matrix @ y_vector
    z_transformed = rotation_matrix @ z_vector

    x_color = [255, 0, 0]  # Red
    y_color = [0, 255, 0]  # Green
    z_color = [0, 0, 255]

    # Log the arrows
    rr.log(f"transformation/{name}", rr.Arrows3D(vectors=[x_transformed, y_transformed, z_transformed], origins=[translation_vector, translation_vector, translation_vector], colors=[x_color, y_color, z_color]))

def animate_joints(duration=10.0, fps=30):
    """Animate all joints simultaneously with smooth motion"""
    print(f"Starting simultaneous joint animation for {duration} seconds...")
    
    dt = 1.0 / fps
    total_steps = int(duration * fps)
    
    for step in range(total_steps):
        t = step / total_steps  # Normalized time from 0 to 1
        
        # Calculate angles for each joint using different wave patterns
        joint_angles = {}
        
        # Each joint follows a different sinusoidal pattern
        for i, (joint_key, joint_info) in enumerate(joint_limits.items()):
            lower = joint_info["lower"]
            upper = joint_info["upper"]
            center = (upper + lower) / 2
            amplitude = (upper - lower) / 3  # Use 1/3 of range for safety
            
            # Different frequency and phase for each joint
            frequency = 0.5 + i * 0.1  # Different speeds
            phase = i * np.pi / 3  # Different phase offsets
            
            angle = center + amplitude * np.sin(2 * np.pi * frequency * t + phase)
            joint_angles[joint_key] = angle
        
        # Set all joints at once
        set_joints(joint_angles)
        
        # Progress indicator
        if step % (fps // 2) == 0:  # Print every 0.5 seconds
            progress = (step / total_steps) * 100
            print(f"Progress: {progress:.1f}%")
        
        time.sleep(dt)

# Main execution
if __name__ == "__main__":
    print("SO101 Simultaneous Joint Movement Demo")
    print("======================================")
    
    # Start with all joints at zero
    print("Initializing all joints to zero position...")
    zero_pose = {joint: 0.0 for joint in joint_limits.keys()}
    set_joints(zero_pose)
    time.sleep(2.0)
    
    # Demo 3: Continuous animation
    animate_joints(duration=8.0, fps=30)
    
    # Return to zero
    print("\nReturning to zero position...")
    set_joints(zero_pose)
    
    print("\nDemo complete! All joints moved simultaneously.")