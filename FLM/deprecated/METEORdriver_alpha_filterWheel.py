
from odemis.driver.actuator import FixedPositionsActuator


from odemis.driver.tmcm import TMCLController
CONFIG= {
    "name":"Optical_Actuator",
    "role":"null",
    "port": "/dev/ttyTMCM*",
    "address": None,
    "axes": ["fw"],
    # TODO: check step size, so that 6.28 rad == one full rotation
    "ustepsize": [1.227184e-6], # [rad/µstep]
    "rng": [[-7, 14]], # rad, more than 0->2 Pi, in order to allow one extra rotation in both direction, when quickly swit
    "unit": ["rad"],
    "refproc": "Standard",
    "refswitch": {"fw": 4}
}

controler=TMCLController(**CONFIG)

# CONFIG2 = {
#    "name": "wheel", 
#    "role": "filter",  
#    "dependencies": {"band": "Optical_Actuator"},
#    "axis_name": "fw",
#    "positions": {
#        # TODO: check filters
#        # pos (rad) -> m,m
#        3.857177647: [420.e-9, 460.e-9], # FF01-440/40-25
#        3.071779484: [510.e-9, 540.e-9], # FF01-525/30-25
#        2.286381320: [589.e-9, 625.e-9], # FF01-607/36-25
#        1.500983157: [672.e-9, 696.e-9], # FF02-684/24-25
#    },
#    "cycle":"6.283185"

                
# }




# wheel=FixedPositionsActuator(**CONFIG2)