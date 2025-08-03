"""Hand Tracker using MediaPipe to detect hand positions in images."""

import cv2
import mediapipe as mp
import numpy as np
import time

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


class HandTracker:
    """Hand Tracker using MediaPipe Hands to detect hand positions."""

    def __init__(self, nb_hands=1, tap_threshold=0.3, hold_threshold=1.0, distance_threshold=0.05):
        """Initialize the Hand Tracker."""
        self.hands = mp_hands.Hands(
            static_image_mode=False, max_num_hands=nb_hands, min_detection_confidence=0.5
        )
        self.tap_threshold = tap_threshold
        self.hold_threshold = hold_threshold
        self.distance_threshold = distance_threshold
        self.finger_down_start = None
        self.is_finger_down = False
        
        # Cached values updated by update()
        self.current_distance = None
        self.current_duration = 0.0
        self.index_pos = None
        self.thumb_pos = None
        self.just_tapped = False

    def get_hands_positions(self, img):
        """Get the positions of the hands in the image."""
        img = cv2.flip(img, 1)

        results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks is not None and results.multi_handedness is not None:
            palm_centers = []
            for landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Only process right hand
                if handedness.classification[0].label != 'Right':
                    continue
                middle_finger_pip_landmark = landmarks.landmark[
                    mp_hands.HandLandmark.MIDDLE_FINGER_PIP
                ]
                palm_center = np.array(
                    [middle_finger_pip_landmark.x, middle_finger_pip_landmark.y]
                )

                # Normalize the palm center to the range [-1, 1]
                # Flip the x-axis
                palm_center = [-(palm_center[0] - 0.5) * 2, (palm_center[1] - 0.5) * 2]
                palm_centers.append(palm_center)

            return palm_centers
        return None

    def update(self, img):
        """Update all hand tracking data from the image."""
        img = cv2.flip(img, 1)
        
        results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        current_time = time.time()
        self.just_tapped = False
        
        if results.multi_hand_landmarks is not None and results.multi_handedness is not None:
            for landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Only process right hand
                if handedness.classification[0].label != 'Right':
                    continue
                index_tip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                
                self.index_pos = np.array([index_tip.x, index_tip.y])
                self.thumb_pos = np.array([thumb_tip.x, thumb_tip.y])
                self.current_distance = np.linalg.norm(self.index_pos - self.thumb_pos)
                
                # Update gesture state
                if not self.is_finger_down and self.current_distance < self.distance_threshold:
                    self.is_finger_down = True
                    self.finger_down_start = current_time
                    
                if self.is_finger_down:
                    if self.finger_down_start is not None:
                        self.current_duration = current_time - self.finger_down_start
                    else:
                        self.current_duration = 0.0
                        
                    if self.current_distance > self.distance_threshold:
                        # Check if this was a tap before resetting
                        if self.current_duration < self.tap_threshold:
                            self.just_tapped = True
                        self._reset_finger_state()
                else:
                    self.current_duration = 0.0
                    
                return
        
        # No hands detected
        self._reset_finger_state()
        self.current_distance = None
        self.current_duration = 0.0
        self.index_pos = None
        self.thumb_pos = None

    def isTap(self):
        """Check if a tap gesture just occurred."""
        return self.just_tapped

    def isHold(self):
        """Check if a hold gesture is currently occurring."""
        if (self.is_finger_down and 
            self.current_distance is not None and 
            self.current_distance < self.distance_threshold and 
            self.current_duration >= self.hold_threshold):
            return True
        return False

    def _reset_finger_state(self):
        """Reset the finger tracking state."""
        self.finger_down_start = None
        self.is_finger_down = False
        self.current_duration = 0.0
