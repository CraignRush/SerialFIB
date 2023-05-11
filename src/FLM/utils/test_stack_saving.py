import numpy as np
import tifffile as tif
from scipy.ndimage import rotate
import cv2

img = np.array(cv2.imread('test.tiff', cv2.IMREAD_GRAYSCALE))
img =  np.expand_dims(img, axis=2)
stack = np.concatenate((img, img, img), axis=2)
stack = np.concatenate((stack, rotate(img, 90, reshape=False)),axis=2)
stack = np.concatenate((stack, rotate(img, -90, reshape=False)),2)
stack = np.expand_dims(stack,0)
stack = np.expand_dims(stack,0)
stack = np.moveaxis(stack,-1,0)

print(stack.shape)

z_distance = 4.0  # TODO set correctly
stack_order = 'TZCXY'  # obviously cannot be changed...
fps = 10.0
tif.imsave('test2.tiff', stack, imagej=True, resolution=(1.0/4.107142857142857e-02, 1.0/4.107142857142857e-02),\
    photometric='minisblack',\
    metadata={'spacing': z_distance, 'unit': 'um','axes': stack_order, 'finterval': fps})