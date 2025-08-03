import numpy as np

# Camera calibration parameters
# Obtained from camera calibration with RMS re-projection error: 0.866506
# Mean reprojection error: 0.115354

CAMERA_MATRIX = np.array([
    [601.572335,     0.0,         937.03675793],
    [0.0,            601.56643387, 527.30679894],
    [0.0,            0.0,          1.0]
], dtype=np.float32)

DISTORTION_COEFFS = np.array([
    -0.05123108, 0.07768729, -0.0076664, 0.00367755, -0.05111074
], dtype=np.float32)

# Camera parameters breakdown:
# fx = 601.572335 (focal length in x-direction, pixels)
# fy = 601.56643387 (focal length in y-direction, pixels)
# cx = 937.03675793 (principal point x-coordinate, pixels)
# cy = 527.30679894 (principal point y-coordinate, pixels)

# Distortion coefficients: [k1, k2, p1, p2, k3]
# k1, k2, k3: radial distortion coefficients
# p1, p2: tangential distortion coefficients