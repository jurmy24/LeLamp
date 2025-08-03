import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R

def draw_hand(img, hand, is_tap=False, is_hold=False):
    """Draw debug information on the image."""
    h, w, _ = img.shape
    draw_palm = [(-hand[0] + 1) / 2, (hand[1] + 1) / 2]  # [0, 1]
    
    # Change palm color based on gesture
    palm_color = (0, 0, 255)  # Default red
    if is_tap:
        palm_color = (0, 255, 255)  # Yellow for tap
    elif is_hold:
        palm_color = (255, 0, 255)  # Magenta for hold
    
    cv2.circle(
        img,
        (int(w - draw_palm[0] * w), int(draw_palm[1] * h)),
        radius=8,
        color=palm_color,
        thickness=-1,
    )
    
    # Draw gesture status
    draw_gesture_status(img, is_tap, is_hold)


def draw_gesture_status(img, is_tap, is_hold):
    """Draw gesture status text on the image."""
    h, w, _ = img.shape
    
    # Status text
    if is_tap:
        status_text = "TAP!"
        color = (0, 255, 255)  # Yellow
    elif is_hold:
        status_text = "HOLD!"
        color = (255, 0, 255)  # Magenta
    else:
        status_text = "Watching..."
        color = (255, 255, 255)  # White
    
    cv2.putText(img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    
    # Instructions
    instructions = [
        "Pinch index & thumb together:",
        "Quick pinch = TAP (yellow)",
        "Long pinch = HOLD (magenta)",
        "Press 'q' to quit"
    ]
    
    for i, instruction in enumerate(instructions):
        cv2.putText(img, instruction, (10, h - 100 + i * 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def draw_finger_tips(img, hand_tracker, is_hold=False):
    """Draw finger tips and distance between them."""
    if hand_tracker.index_pos is None or hand_tracker.thumb_pos is None:
        return
    
    h, w, _ = img.shape
    
    # Convert normalized coordinates to pixel coordinates
    # Note: MediaPipe coordinates are already processed with flipped image
    index_pixel = (int(w - hand_tracker.index_pos[0] * w), int(hand_tracker.index_pos[1] * h))
    thumb_pixel = (int(w - hand_tracker.thumb_pos[0] * w), int(hand_tracker.thumb_pos[1] * h))
    
    # Draw finger tip circles
    cv2.circle(img, index_pixel, 8, (0, 255, 0), -1)  # Green for index
    cv2.circle(img, thumb_pixel, 8, (255, 255, 0), -1)  # Cyan for thumb
    
    # Draw line between finger tips
    cv2.line(img, index_pixel, thumb_pixel, (255, 255, 255), 2)
    
    # Calculate midpoint between finger tips
    mid_x = (index_pixel[0] + thumb_pixel[0]) // 2
    mid_y = (index_pixel[1] + thumb_pixel[1]) // 2
    midpoint = (mid_x, mid_y)
    
    # Draw error line from center of screen to midpoint when holding
    if is_hold:
        center = (w // 2, h // 2)
        cv2.line(img, center, midpoint, (255, 0, 0), 3)  # Red error line
        cv2.circle(img, center, 5, (255, 0, 0), -1)  # Red center point
        cv2.circle(img, midpoint, 5, (255, 0, 0), -1)  # Red midpoint
        
        # Show error distance
        error_distance = np.sqrt((mid_x - center[0])**2 + (mid_y - center[1])**2)
        cv2.putText(img, f"Error: {error_distance:.1f}px", (center[0] + 10, center[1] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    # Calculate and display distance
    if hand_tracker.current_distance is not None:
        distance_text = f"Distance: {hand_tracker.current_distance:.3f}"
        duration_text = f"Duration: {hand_tracker.current_duration:.2f}s"
        
        cv2.putText(img, distance_text, (mid_x - 50, mid_y - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, duration_text, (mid_x - 50, mid_y + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Draw labels
    cv2.putText(img, "INDEX", (index_pixel[0] - 30, index_pixel[1] - 15), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    cv2.putText(img, "THUMB", (thumb_pixel[0] - 30, thumb_pixel[1] - 15), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
