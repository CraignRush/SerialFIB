from typing import List, Tuple
import numpy as np
from scipy import optimize


def dict_2_numpy(d: dict = {'x':0.0,'y':0.0,'z':0.0},dims: int = 5):
    """Convert the stage position dict to a numpy vector with dims entrys"""
    if isinstance(d,dict) and (dims == 5):
        v = np.array((d['x'],d['y'],d['z'],d['t'],d['r']))
    elif isinstance(d,dict) and (dims == 3):
        v = np.array((d['x'],d['y'],d['z']))
    elif isinstance(d,dict) and (dims == 2): 
        v = np.array((d['x'],d['y']))
    else:
        v = np.array(())
    return v

def numpy_2_dict(p: np.ndarray):
    if p.size == 5:        
        d = {'x':p[0],'y':p[1],'z':p[2],'t':p[3],'r':p[4]}
    elif p.size == 3:
        d = {'x':p[0],'y':p[1],'z':p[2],'t':p[3],'r':p[4]}
    elif p.size == 2:        
        d = {'x':p[0],'y':p[1],'z':0.0,'t':0.0,'r':0.0}
    return d

def get_rotation_coord(point: dict, theta: int, cor: np.ndarray = np.array( (0,0) ) , returnDict: int = 0): #-> np.ndarray | dict:
    """ Get the compucentrically rotated coordinates of a rotation change"""

    p = dict_2_numpy(point, 3)

    #expand dimension for offset computation
    if p.size == 3:
        p = np.append(p,1)
    elif p.size == 2:
        p = np.append(p,(0,1))    
    else: 
        raise Exception("wrong Point format")
    

    t   = np.radians(theta)
    c, s    = np.cos(t), np.sin(t)
    #construct rotation matrix
    R       = np.array(( (c,-s,0,0), (s,c,0,0), (0,0,1,0), (0,0,0,1) ))
    x0      = cor[0]
    y0      = cor[1]
    T       = np.identity(4)
    T_neg   = np.identity(4)
    T[3][0] = x0
    T[3][1] = y0
    T_neg[0][3] = -x0
    T_neg[1][3] = -y0

    result = np.append(np.dot(T,np.dot(R,np.dot(T_neg,p)))[0:3],(0.0,t),axis=0)
    #tmp = result[0]
    #result[0] = result[1]
    #result[1] = tmp
    if returnDict == True:
        result =  numpy_2_dict(result)

    return result


def get_tilt_coord(point: np.ndarray, phi: int, cor: np.ndarray):
    """ Get the compucentrically rotated coordinates of a tilt change"""
    t       = np.radians(phi)
    c, s    = np.cos(t), np.sin(t)
    R       = np.array(( (1,0,0,0), (0,c,-s,0), (0,s,c,0), (0,0,0,1) ))
    off     = np.array( (0,  cor[0],  cor[1], 1) )
    off_neg = np.array( (0, -cor[0], -cor[1], 1) )
    T       = np.stack( (np.identity(3), off ) , axis=1)
    T_neg   = np.stack( (np.identity(3), off_neg), axis=1)

    return np.dot(np.dot(np.dot(point, T_neg),R),T)


def get_center_of_rotation(points: np.ndarray) -> Tuple[dict, float, float]:
    "Computes the center of rotation, error and radius from (x,y) coordinates"
    CoR, radius, error = _fit_LSQ_circle(points[0:2,:])
    #CoR = numpy_2_dict(CoR)

    return CoR, error, radius


def _fit_LSQ_circle(points: np.ndarray = np.array( (2,1) )):
    """Least-square fit of a circle to the given coordinates"""
    # coordinates of the barycenter
    x_m = np.mean(points[0,:])
    y_m = np.mean(points[1,:])

    def calc_R(xc, yc):
        """ calculate the distance of each 2D points from the center (xc, yc) """
        return np.sqrt((points[0,:]-xc)**2 + (points[1,:]-yc)**2)

    def f_2(c):
        """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
        Ri = calc_R(*c)
        return Ri - Ri.mean()

    center_estimate = x_m, y_m
    center_2, ier = optimize.leastsq(f_2, center_estimate)

    xc_2, yc_2 = center_2
    Ri_2       = calc_R(*center_2)
    R_2        = Ri_2.mean()
    residu_2   = sum((Ri_2 - R_2)**2)

    return center_2, R_2, residu_2

