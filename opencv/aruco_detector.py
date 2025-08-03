#!/usr/bin/env python3
import cv2
import numpy as np
from .camera_params import CAMERA_MATRIX, DISTORTION_COEFFS

class ArucoDetector:
    def __init__(self, camera_id=0, marker_size=0.025):
        """
        Initialize ArUco detector.
        
        Args:
            camera_id: Camera device ID
            marker_size: Size of ArUco marker in meters
        """
        self.camera_id = camera_id
        self.marker_size = marker_size
        self.camera_matrix = CAMERA_MATRIX
        self.dist_coeffs = DISTORTION_COEFFS
        
        # Initialize camera
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_id}")
        
        # Initialize ArUco detector with high sensitivity
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        
        # High sensitivity parameters
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 23
        self.aruco_params.adaptiveThreshWinSizeStep = 10
        self.aruco_params.adaptiveThreshConstant = 7
        
        # Corner refinement
        self.aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.aruco_params.cornerRefinementWinSize = 5
        self.aruco_params.cornerRefinementMaxIterations = 30
        self.aruco_params.cornerRefinementMinAccuracy = 0.1
        
        # Detection sensitivity
        self.aruco_params.minMarkerPerimeterRate = 0.03
        self.aruco_params.maxMarkerPerimeterRate = 4.0
        self.aruco_params.polygonalApproxAccuracyRate = 0.03
        self.aruco_params.minCornerDistanceRate = 0.05
        self.aruco_params.minDistanceToBorder = 3
        
        # Error correction
        self.aruco_params.maxErroneousBitsInBorderRate = 0.35
        self.aruco_params.minOtsuStdDev = 5.0
        
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
    
    def _rodrigues_to_transform_matrix(self, rvec, tvec):
        """Convert rotation vector and translation vector to 4x4 transformation matrix"""
        # Convert rotation vector to rotation matrix
        R, _ = cv2.Rodrigues(rvec)
        
        # Create 4x4 transformation matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = tvec.flatten()
        
        return T
    
    def get_pos(self):
        """
        Get positions of all detected ArUco markers as 4x4 transformation matrices.
        
        Returns:
            dict: Dictionary with marker IDs as keys and 4x4 transformation matrices as values
                  Returns None if no frame can be captured
        """
        # Capture frame
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Detect ArUco markers
        corners, ids, _ = self.detector.detectMarkers(frame)
        
        marker_poses = {}
        
        if ids is not None and len(ids) > 0:
            # Estimate pose for each marker
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners, self.marker_size, self.camera_matrix, self.dist_coeffs
            )
            
            # Convert to 4x4 transformation matrices
            for i, marker_id in enumerate(ids):
                marker_id = int(marker_id[0])
                T = self._rodrigues_to_transform_matrix(rvecs[i], tvecs[i])
                marker_poses[marker_id] = T
            
            # Draw markers and axes on frame
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            for i in range(len(ids)):
                cv2.drawFrameAxes(
                    frame, self.camera_matrix, self.dist_coeffs,
                    rvecs[i], tvecs[i], self.marker_size * 0.5
                )
                
                # Add marker info text
                corner = corners[i][0][0]
                text_pos = (int(corner[0]), int(corner[1]) - 10)
                marker_id = int(ids[i][0])
                distance = np.linalg.norm(tvecs[i])
                
                cv2.putText(frame, f"ID:{marker_id}", text_pos, 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(frame, f"Dist:{distance:.3f}m", 
                           (text_pos[0], text_pos[1] + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Show frame
        cv2.imshow('ArUco Detection', frame)
        cv2.waitKey(1)
        
        return marker_poses
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = ArucoDetector()
    
    print("Press 'q' to quit")
    
    try:
        while True:
            poses = detector.get_pos()
            
            if poses:
                print(f"Detected {len(poses)} markers:")
                for marker_id, transform in poses.items():
                    position = transform[:3, 3]
                    print(f"  Marker {marker_id}: pos=({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f})")
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        pass
    
    finally:
        del detector