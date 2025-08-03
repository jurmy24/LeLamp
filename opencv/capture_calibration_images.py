#!/usr/bin/env python3
import cv2
import os
import argparse

def capture_calibration_images(num_images=20, output_dir="./images"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print(f"Camera opened successfully. Capturing {num_images} calibration images.")
    print("Press ENTER to capture an image, 'q' to quit early")
    
    captured_count = 0
    
    while captured_count < num_images:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        cv2.imshow('Calibration Image Capture', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("Quitting early...")
            break
        elif key == 13:  # Enter key
            filename = os.path.join(output_dir, f"calibration_{captured_count:03d}.jpg")
            cv2.imwrite(filename, frame)
            captured_count += 1
            print(f"Captured image {captured_count}/{num_images}: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"Capture complete. {captured_count} images saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture calibration images for camera calibration")
    parser.add_argument("-n", "--num_images", type=int, default=20, 
                       help="Number of images to capture (default: 20)")
    parser.add_argument("-o", "--output_dir", type=str, default="./images",
                       help="Output directory for images (default: ./images)")
    
    args = parser.parse_args()
    
    capture_calibration_images(args.num_images, args.output_dir)