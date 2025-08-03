"""Hand Tracker App

This app tracks your hand using a camera.

It uses OpenCV camera to detect the hand position.
It uses mediapipe to track the hand and OpenCV for image processing.
"""

import threading

import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R

from hand_tracking.hand_tracker import HandTracker
from hand_tracking.draw_utils import draw_hand, draw_finger_tips, draw_gesture_status

from tools.config_loader import get_config_loader 

from lerobot.robots.lelamp_follower import LeLampFollowerConfig, LeLampFollower
from lerobot.teleoperators.lelamp_leader import LeLampLeaderConfig, LeLampLeader

# PID Parameters
kp = 20
max_delta = 10

# Init Camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No camera found. Please connect a camera.")

hand_tracker = HandTracker(distance_threshold=0.1)

# Init robot device
robot_config = get_config_loader().get_follower_config()
robot_config = LeLampFollowerConfig(
    port=robot_config.port,
    id=robot_config.id,
)
robot = LeLampFollower(robot_config)
robot.connect(calibrate=False)

action = None

# Get robot observation
observation = robot.get_observation()


# Copy into action if ends with .pos or .intensity
action = {k: v for k, v in observation.items() if k.endswith(".pos") or k.endswith(".intensity")}

# Light State
is_light_on = False
while True:

    # print("Robot observation:", observation)

    # Capture current camera frame
    success, img = cap.read()

    if not success:
        print("Failed to capture image from camera.")
        continue
    
    # Update hand tracker with current frame
    hand_tracker.update(img)
    hands = hand_tracker.get_hands_positions(img)

    # Check for tap and hold gestures
    is_tap = hand_tracker.isTap()
    is_hold = hand_tracker.isHold()

    if is_tap:
        is_light_on = not is_light_on
        print("TAP detected!")

    if is_hold and hands and hand_tracker.index_pos is not None:
        hand = hands[0]  # Assuming we only track the first detected hand

        draw_hand(img, hand, is_tap, is_hold)
        draw_finger_tips(img, hand_tracker, is_hold)

        error = hand_tracker.index_pos - [0.5, 0.5]  # Centered at (0.5, 0.5)
        
        # If error is too small, reset to zero
        error_threshold = 0.05
        if abs(error[0]) < error_threshold:
            error[0] = 0
        if abs(error[1]) < error_threshold:
            error[1] = 0
        
        print("Hand position error:", error)
        error[0] = kp * error[0]
        error[1] = kp * error[1]
        error = np.clip(error, -max_delta, max_delta)

        print("Error:", error)
        action["shoulder_pan.pos"] += error[0]
        action["wrist_flex.pos"] += - error[1]

        # Ensure action values are within the range [-100, 100]
        action["shoulder_pan.pos"] = np.clip(action["shoulder_pan.pos"], -100, 100)
        action["wrist_flex.pos"] = np.clip(action["wrist_flex.pos"], -100, 100)

        print("Action after error correction:", action["shoulder_pan.pos"], action["wrist_flex.pos"])


        pass
    else:
        draw_gesture_status(img, is_tap, is_hold)
        draw_finger_tips(img, hand_tracker, is_hold)

    if is_light_on:
        action["led.intensity"] = 50
    else:
        action["led.intensity"] = 0
    # Send action to robot
    robot.send_action(action)   

    cv2.imshow("Hand Tracker App", img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break