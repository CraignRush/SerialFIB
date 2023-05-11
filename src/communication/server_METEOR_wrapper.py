from tokenize import Floatnumber
import cv2
from ..FLM import FLM
from ..utils.config import LOCAL_DEV
from .data_container import TCP_Package
from ..utils.logger import logger_server
import numpy as np
import datetime


def execute_python_code(script, returnVal = 'r' ):
    logger_server.debug("Executing code: %s",script)
    loc = {}
    exec(script, globals(), loc)
    if loc != {}:
        return loc[returnVal]
    else:
        return -1

def get_image(METEOR):
    # TODO implement properly
    if (LOCAL_DEV) or (METEOR == None):
        img = np.array(cv2.imread('test.tiff',cv2.IMREAD_GRAYSCALE))
    else:   
        img = np.array(METEOR.testSingleImage(),dtype='uint8').copy(order='C')
    return img


def get_image_stack(METEOR: FLM, stack_length: float, stack_step: float):
    # TODO implement properly    
    logger_server.warning('ASK SVEN ABOUT THIS BEHAVIOUR')
    if (LOCAL_DEV) or (METEOR == None):
        from scipy.ndimage import rotate
        img = np.array(cv2.imread('test.tiff',cv2.IMREAD_GRAYSCALE))
        stack = np.tile(img,(3,1,1))
        stack = np.concatenate((stack,np.expand_dims(rotate(img,90,reshape=False),0)))      
        stack = np.concatenate((stack,np.expand_dims(rotate(img,-90,reshape=False),0)))
    else:   
        stack= np.array(METEOR.start_acquistion(stack_length,stack_step),dtype='uint16').copy(order='C')
        #stack = METEOR.testStack2(2,1)
    return stack

def set_focus(METEOR: FLM,val: float):
    # TODO implement properly
    if isinstance(val, float):
        return 0
    else:
        return -1

def set_focus_auto(METEOR: FLM, logger):
    # TODO implement properly
    try:
        METEOR.autofocus()
    except: 
        logger.error("Autofocus failed")
        return -1
    finally:
        return 0

def set_intensity(METEOR: FLM,val):
    # TODO implement properly    
    if (val >= 0) and (val < 256) and isinstance(val, int):
        return 0
    else:
        return -1

def set_exposure(METEOR: FLM,val:float):
    # TODO implement properly
    if  (val > 0) and (val < 10000) and isinstance(val, float):
        METEOR.setCameraExposure(val)
        return 0
    else:
        return -1

def set_fluo_color(METEOR: FLM,color:str):
    if isinstance(color, METEOR.fluorescence):
        METEOR.set_channel(color)
        return 0
    else:
        return -1
    
def parsePackage(p,METEOR,logger=logger_server):
    if  not isinstance(p,TCP_Package):
        logger.error("Unrecognized or corrupted package")
        return -1
    elif p.cmd == 'PYTHONCODE':
        #TODO execute custom python code from "data'
        return TCP_Package('RESULT PYTHONCODE',execute_python_code(p.data))
    elif p.cmd == 'ACQUIRE':
        #TODO acquire and transfer image
        img = get_image(METEOR)
        return TCP_Package('IMAGE', img, NP_shape=img.shape, NP_dtype=img.dtype)
    elif p.cmd == 'ACQUIRE_Z':
        #TODO acquire z stack with focus points (tuple of float) from data
        stack_length = p.data[0]
        stack_step = p.data[1]
        stack = get_image_stack(METEOR,stack_length, stack_step)
        return TCP_Package('ZSTACK', stack, NP_shape=stack.shape, NP_dtype=stack.dtype)
    elif p.cmd == 'SET_FOCUS':
        #TODO set the focus postition from data float
        return TCP_Package('STATE',set_focus(METEOR,float(p.data)))
    elif p.cmd == 'SET_INTENSITY':
        #TODO set the light intensity float
        result = set_intensity(METEOR,int(p.data))        
    elif p.cmd == 'SET_FLUOCOLOR':
        #TODO set the light intensity float
        result = set_fluo_color(METEOR,p.data)
    elif p.cmd == 'SET_EXPOSURE':
        #TODO set the exposure time        
        return TCP_Package('STATE',set_exposure(METEOR,int(p.data)))
    elif p.cmd == 'AUTOFOCUS':
        #TODO set the exposure time        
        return TCP_Package('STATE',set_focus_auto(METEOR,logger))
    elif p.cmd == 'IMAGE':
        #process received image
        filename = "img/" + datetime.now() +".tiff"
        with open(filename, "wb") as f:
            f.write(p.data)
        return TCP_Package()
    elif p.cmd == 'ZSTACK':
        #process stack
        filename = "stack/" + datetime.now() +".tiff"
        with open(filename, "wb") as f:
            f.write(p.data)
        return TCP_Package('File written')
    else:
        return TCP_Package('Unrecognized command')

