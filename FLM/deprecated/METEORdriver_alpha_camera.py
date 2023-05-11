from odemis.driver.ueye import Camera
import matplotlib.pyplot as plt
import numpy as np

CONFIG = {
        'name':'camera',
        'role':'ccd',
        'device': '4103458147',
        'transp': [2, 1]
        }


cam=Camera(**CONFIG)
cam.GetCameraInfo()

image=cam.data.get()




plt.imshow(image)
plt.show()

