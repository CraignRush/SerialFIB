import cv2
from scipy import optimize
import numpy as np
from matplotlib import pyplot as plt


def matchFeatures(img_to_align: np.ndarray, img_reference: np.ndarray, MIN_MATCHES=50, N_FEATURES=5000,DIST_THRES=0.7,VERBOSE=False, DISPLAY_MATCHES=False) -> np.ndarray:
    '''
    Returns: Corrected_img, mat
    Corrected_img: The warped image to the detected position of the reference.
    Mat: The perspective transformation matrix. The top left 2x2 sub-matrix is a rotation matrix. The right colum is the
    translation in homogeneous coordinates and the bottom indices 2,0 and 2,1 contain the projection vector.

    This function uses the OpenCV implementation of the unpatented Oriented FAST and Rotated BRIEF algorithms
    (ORB, Rublee,2011) together with a nearest neighbor matcher(Fast Library for Approximate Nearest Neighbors (FLANN)).
    ORB uses the on the well-known Features from Accellerated Segmentation Test (FAST) keypoint detector and 
    the Binary Robust Independent Elementary Features (BRIEF) descriptor. Due to the patch orientation, the BRIEF
    algorithm looses its invariance to rotation and hence performed best out of tested SURF and SIRT algorithms.  
    This function finds the homography from two given images (img_to_alig is aligned to the img_reference). 
    MIN_MATCHES: Minimal number of "good" matching features in both images
    N_FEATURES: Initally detected features per image
    DIST_THRES: "Goodness" parameter (the lower the better, can be increase if matcher is to critical)
    VERBOSE: Prints matching results
    DISPLAY_MATCHES: Creates a figure with connected features from both images.

    '''
    orb = cv2.ORB_create(nfeatures=N_FEATURES)
    kp1, des1 = orb.detectAndCompute(img_to_align, None)
    kp2, des2 = orb.detectAndCompute(img_reference, None)

    index_params = dict(algorithm=6,
                        table_number=6,
                        key_size=12,
                        multi_probe_level=2)
    search_params = {}
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    # As per Lowe's ratio test to filter good matches
    good_matches = []
    for m, n in matches:
        if m.distance < DIST_THRES * n.distance:
            good_matches.append(m)

    if len(good_matches) > MIN_MATCHES:
        src_points = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_points = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        mat, mask = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 10.0)
        corrected_img = cv2.warpPerspective(img_to_align, mat, (img_reference.shape[1], img_reference.shape[0]))
        if DISPLAY_MATCHES:            
            match_img = cv2.drawMatches(img_to_align, kp1, img_reference, kp2, good_matches[:50], None)
            f, ax = plt.subplots()
            ax.imshow(match_img)
            plt.show()
        if VERBOSE:
            print('Matching successful')
        return corrected_img, mat.copy()
    elif DIST_THRES < 0.95: 
        if VERBOSE:       
            print('Matching failed, trying to enlarge threshold for good matches.({})'.format(DIST_THRES+0.1))
        corrected_img, mat = matchFeatures(img_to_align, img_reference, DIST_THRES=DIST_THRES+0.1, DISPLAY_MATCHES=True)
        return corrected_img, mat.copy()
    else:
        if VERBOSE:
            print('Matching failed')
        return None, None

def get_params_from_transformation_matrix(m: np.ndarray, pixel_size=0.0, PRINT=False) -> dict:
    '''
    Deconstructs a given 3x3 perspective transform matrix into the relevant parameters
    Returns: Dict with the parameters:
    't': 2x1 list, Translation in pixel units
    't_meter':2x1 list, Translation in meters (calibrated with given pixel_size parameter)
    'phi': 3x1 list, Calculated, scaled angles from the two rows of the rotation matrix in degrees. Third
    index is the mean rotation angle.
    's': 2x1 Scaling factors in x and y directions
    
    '''
    if np.abs(m[2,0]) > 1e-3 or np.abs(m[2,1]) > 1e-3 :
        print("This is no valid transformation matrix, the projection component is too large.")
        return None
    else:
        a,b,c,d = m[0,0] , m[0,1], m[1,0], m[1,1]
        result = {}
        result['t'] = [m[0,2], m[1,2]]
        sx, sy = np.sqrt(a ** 2 + c ** 2) , np.sqrt(b ** 2 + d ** 2)
        result['s']  = [sx, sy]
        phi1,phi2 = np.rad2deg(np.arctan((c/sx)/(d/sy))), np.rad2deg(np.arctan((-b/sy)/(a/sx)))
        result['phi']  = [phi1,phi2, np.mean([phi1,phi2])]
        result['t_meter'] =[ t * pixel_size for t in result['t']]   

        if PRINT:                        
            print("---Image Transformation---")
            print("{}\n".format(m))
            if pixel_size > 0.0:         
                print("Translation (x,y) / mm: {:.2f}, {:.2f}".format(m[0,2]*1e3*pixel_size,m[1,2]*1e3*pixel_size))
            print("Translation (x,y) / px: {}, {}".format(m[0,2],m[1,2]))
            print("Scaling (x,y): {}, {}".format(result['s'][0], result['s'][1]))
            print("Rotation Angle (x,y, mean): {}, {}, {}".format(phi1,phi2 ,round(result['phi'][2],2)))
        return result        

def calculate_center_lsq(x: list, y: list, VERBOSE= False) -> dict:
    '''
    A simple LSQ fitting of the circle equation resp. the radius and center coordinates from all available points.
    Returns: Dict:
    'x_c','y_c': Center positions
    'r': Circle radius
    'residuum': Remaining error (Sum of squared error)
    '''
    def calc_R(xc, yc):
        """ calculate the distance of each 2D points from the center (xc, yc) """
        return np.sqrt((x-xc)**2 + (y-yc)**2)

    def f_2(c):
        """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
        Ri = calc_R(*c)
        return Ri - Ri.mean()
    # coordinates of the barycenter
    x_m = np.mean(x)
    y_m = np.mean(y)
    center_estimate = x_m, y_m
    center_2, ier = optimize.leastsq(f_2, center_estimate)

    xc_2, yc_2 = center_2
    Ri_2       = calc_R(*center_2)
    R_2        = Ri_2.mean()
    residu_2   = sum((Ri_2 - R_2)**2)

    if VERBOSE:
        print("Center / mm: {},{}".format(xc_2*1e3,yc_2*1e3))
        print("Radius / mm: {}".format(R_2*1e3))
        print("Residuum: {}".format(residu_2))

    return {'xc': xc_2, 'yc': yc_2, 'r': R_2, 'residuum': residu_2}

def rotate_point_around_center(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point
    s, c = np.sin(angle), np.cos(angle)
    qx = ox + c  * (px - ox) - s * (py - oy)
    qy = oy + s * (px - ox) + c * (py - oy)
    return qx, qy