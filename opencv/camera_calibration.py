#!/usr/bin/env python3
import cv2
import numpy as np
import os
import glob
import pickle
import argparse

def calibrate_camera(images_dir="./images", pattern_size=(9, 6), square_size=1.0, save_results=True):
    """
    Calibrate camera using chessboard pattern images.
    
    Args:
        images_dir: Directory containing calibration images
        pattern_size: (width, height) - number of inner corners in chessboard
        square_size: Size of each square in real world units (e.g., mm, cm)
        save_results: Whether to save calibration results to files
    
    Returns:
        ret: RMS re-projection error
        camera_matrix: 3x3 camera intrinsic matrix
        dist_coeffs: Distortion coefficients
        rvecs: Rotation vectors for each image
        tvecs: Translation vectors for each image
    """
    
    # Prepare object points
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    objp *= square_size
    
    # Arrays to store object points and image points from all images
    objpoints = []  # 3D points in real world space
    imgpoints = []  # 2D points in image plane
    
    # Get list of calibration images
    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
    image_files.extend(glob.glob(os.path.join(images_dir, "*.png")))
    
    if not image_files:
        print(f"No images found in {images_dir}")
        return None, None, None, None, None
    
    print(f"Found {len(image_files)} images for calibration")
    
    successful_images = 0
    
    for fname in image_files:
        img = cv2.imread(fname)
        if img is None:
            print(f"Could not read image: {fname}")
            continue
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Find the chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
        
        if ret:
            objpoints.append(objp)
            
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            
            successful_images += 1
            print(f"✓ Found corners in {os.path.basename(fname)}")
        else:
            print(f"✗ Could not find corners in {os.path.basename(fname)}")
    
    if successful_images < 3:
        print(f"Error: Need at least 3 successful images for calibration. Got {successful_images}")
        return None, None, None, None, None
    
    print(f"\nCalibrating camera with {successful_images} images...")
    
    # Calibrate camera
    img_shape = gray.shape[::-1]  # (width, height)
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_shape, None, None)
    
    if ret:
        print(f"✓ Camera calibration successful!")
        print(f"RMS re-projection error: {ret:.6f}")
        print(f"\nCamera Matrix (intrinsics):")
        print(mtx)
        print(f"\nDistortion Coefficients:")
        print(dist.ravel())
        
        # Calculate reprojection error
        mean_error = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
            error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            mean_error += error
        
        mean_error /= len(objpoints)
        print(f"Mean reprojection error: {mean_error:.6f}")
        
        if save_results:
            # Save calibration results
            calibration_data = {
                'camera_matrix': mtx,
                'dist_coeffs': dist,
                'rvecs': rvecs,
                'tvecs': tvecs,
                'rms_error': ret,
                'mean_error': mean_error,
                'image_shape': img_shape,
                'successful_images': successful_images
            }
            
            with open('camera_calibration.pkl', 'wb') as f:
                pickle.dump(calibration_data, f)
            
            # Save as numpy files too
            np.save('camera_matrix.npy', mtx)
            np.save('dist_coeffs.npy', dist)
            
            print(f"\n✓ Calibration data saved to:")
            print(f"  - camera_calibration.pkl")
            print(f"  - camera_matrix.npy")
            print(f"  - dist_coeffs.npy")
    
    return ret, mtx, dist, rvecs, tvecs

def test_calibration(camera_matrix, dist_coeffs, test_image=None):
    """Test calibration by undistorting an image"""
    if test_image is None:
        # Try to use the first calibration image as test
        test_files = glob.glob("./images/*.jpg")
        if not test_files:
            test_files = glob.glob("./images/*.png")
        if not test_files:
            print("No test images found")
            return
        test_image = test_files[0]
    
    img = cv2.imread(test_image)
    if img is None:
        print(f"Could not read test image: {test_image}")
        return
    
    h, w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 1, (w, h))
    
    # Undistort image
    dst = cv2.undistort(img, camera_matrix, dist_coeffs, None, newcameramtx)
    
    # Crop the image
    x, y, w, h = roi
    dst = dst[y:y+h, x:x+w]
    
    # Save result
    cv2.imwrite('undistorted_test.jpg', dst)
    print(f"✓ Test undistortion saved as 'undistorted_test.jpg'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calibrate camera using chessboard images")
    parser.add_argument("-i", "--images_dir", type=str, default="./images",
                       help="Directory containing calibration images")
    parser.add_argument("-w", "--width", type=int, default=9,
                       help="Number of inner corners in width (default: 9)")
    parser.add_argument("-H", "--height", type=int, default=6,
                       help="Number of inner corners in height (default: 6)")
    parser.add_argument("-s", "--square_size", type=float, default=1.0,
                       help="Size of each square in real world units (default: 1.0)")
    parser.add_argument("--test", action="store_true",
                       help="Test calibration with undistortion")
    
    args = parser.parse_args()
    
    pattern_size = (args.width, args.height)
    
    ret, mtx, dist, rvecs, tvecs = calibrate_camera(
        args.images_dir, 
        pattern_size, 
        args.square_size
    )
    
    if ret is not None and args.test:
        test_calibration(mtx, dist)