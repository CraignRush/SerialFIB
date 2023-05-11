from odemis.driver.lle import LLE

CONFIG = {
    "name": "test", 
    "role": "light", 
    "port": "/dev/ttyUSB*", 
    "sources": {"UV": [379.e-9, 384.e-9, 390.e-9, 396.e-9, 401.e-9], # 390/22
                  "cyan": [472.e-9, 479.e-9, 485.e-9, 491.e-9, 497.e-9], # 485/25
                  "green": [544.e-9, 552.e-9, 560.e-9, 568.e-9, 576.e-9], # 560/32
                  "red": [638.e-9, 643.e-9, 648.e-9, 653.e-9, 658.e-9], # 648/20
                 }
                 
}


light=LLE(**CONFIG)
print(light)
#cam.GetCameraInfo()


# turning light on ? 

#light._updatePower((0.295,0,0,0))

# turning light off ? 

#light._updatePower((0,0,0,0))


#light._setSourceIntensity(1,128)

#light.power.range
#Out[25]: ((0.0, 0.0, 0.0, 0.0), (0.295, 0.196, 0.26, 0.231))

