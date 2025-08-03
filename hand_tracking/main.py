"""Hand Tracker App

This app tracks your hand using a camera.

It uses OpenCV camera to detect the hand position.
It uses mediapipe to track the hand and OpenCV for image processing.
"""

import threading

import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R

from hand_tracker import HandTracker

gui = True  # Set to True if you want to use the GUI for debugging

class HandTrackerApp:
    # Proportional gain for the controller
    # Reduce/Increase to make the head movement smoother or more responsive)
    kp = 0.2

    # Maximum delta for the head position adjustments
    # This limits how much the head can move in one iteration to prevent abrupt movements
    max_delta = 0.3

    # Proportional gains for the head height adjustment
    # Adjust this value to control how much the head moves up/down based on vertical error
    kz = 0.04

    def run(self, stop_event: threading.Event):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("No camera found. Please connect a camera.")

        hand_tracker = HandTracker()

        head_pose = np.eye(4)
        euler_rot = np.array([0.0, 0.0, 0.0])

        while not stop_event.is_set():
            success, img = cap.read()

            if not success:
                print("Failed to capture image from camera.")
                continue

            # Update hand tracker with current frame
            hand_tracker.update(img)
            
            # Check for tap and hold gestures
            is_tap = hand_tracker.isTap()
            is_hold = hand_tracker.isHold()
            
            if is_tap:
                print("TAP detected!")
            if is_hold:
                print("HOLD detected!")

            hands = hand_tracker.get_hands_positions(img)
            if hands:
                hand = hands[0]  # Assuming we only track the first detected hand

                if gui:
                    draw_hand(img, hand, is_tap, is_hold)
                    draw_finger_tips(img, hand_tracker, is_hold)

                error = np.array([0, 0]) - hand
                error = np.clip(
                    error, -self.max_delta, self.max_delta
                )  # Limit error to avoid extreme movements
                euler_rot += np.array(
                    [0.0, -self.kp * 0.1 * error[1], self.kp * error[0]]
                )

                head_pose[:3, :3] = R.from_euler(
                    "xyz", euler_rot, degrees=False
                ).as_matrix()
                head_pose[:3, 3][2] = (
                    error[1] * self.kz
                )  # Adjust height based on vertical error

                # Robot head movement disabled
                # reachy_mini.set_target(head=head_pose)
                pass
            else:
                if gui:
                    draw_gesture_status(img, is_tap, is_hold)
                    draw_finger_tips(img, hand_tracker, is_hold)

            if gui:
                cv2.imshow("Hand Tracker App", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        
        cap.release()
        cv2.destroyAllWindows()


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


if __name__ == "__main__":
    # You can run the app directly from this script
    app = HandTrackerApp()
    stop = threading.Event()

    try:
        print("Running Hand Tracker App...")
        print("Press Ctrl+C to stop the app.")
        app.run(stop)
        print("App has stopped.")

    except KeyboardInterrupt:
        print("Stopping the app...")
        stop.set()