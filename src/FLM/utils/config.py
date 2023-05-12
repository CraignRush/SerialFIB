import logging


# xT Stage Coordinates
SAMPLE_CENTERS = {"GRID 1": {'x': -3.e-3, 'y': 2.56e-3, 'z': 6.97e-3},
                  "GRID 2": {'x': 2.98e-3, 'y': 2.46e-3, 'z': 6.96e-3}}
# ODEMIS Mirroring values (X/Y) between SEM - METEOR
POS_COR = [24.4925e-3, 0.0641e-3] #m


# TCP/IP Connection protocl
TCP_BUFFER = int(40980000)  # int(1048576)
LOGGER_NAME_CLIENT = 'COMLOG_CLIENT'
LOGGER_NAME_SERVER = 'COMLOG_SERVER'
LOGGING_LEVEL = logging.DEBUG
LOCAL_DEV = False
DISPLAY_PROGESS = False
SAVE_DEBUGGING_IMAGES = False
ENCRYPTION = False
SERVER_PORT = 53215
if LOCAL_DEV:
    SERVER_IP = "127.0.0.1"
else:
    SERVER_IP = "10.37.0.105"

PICKLE_PROTOCOL = 4
CODEC = 'base64_codec'


# METEOR CONFIG
SAVE_DEBUGGING_IMAGES = False
ROUGH_FOCUS_POS = 10.5e-3  # focus pos in m
EMISSION_RAD = (0.08, 0.865398, 1.650796, 2.4361944)
EMISSION = {'green': 0, 'ref': 1, 'orange': 2, 'red': 3} # Filter positions{'green': 2, 'ref': 3, 'orange': 1, 'red': 0} # Filter positions
EXCITATION = {'UV': 3, 'cyan': 2, 'green': 1, 'red': 0} # Lumencor parameters.
CAMERA = {'name': 'Camera',
          'role': 'ccd',
          #        device: null, # Any one found will do, otherwise, put the serial number
          'device': "4103458147",  # Pick the right  IDS according to the serial number
          # 'transp': [-1, -2],  # To swap/invert axes
          # 'ROTATION': -0.099484,  # [rad] (=5.7°)
          }

FOCUS = {  # CLS3252dsc-1
    'name': 'Optical Focus',
    'role': 'focus',
    'locator': 'network:sn:MCS2-00003632',
    # 'locator': "fake",
    'ref_on_init': True,
    'axes': {
        'z': {
            # 0 is safely parked (FAV_POS_DEACTIVE)
            # 17mm is typically in focus (FAV_POS_ACTIVE)
            'range': [-1.e-3, 20.e-3],
            'unit': 'm',
            'channel': 0
        },
    },
    # TODO: check speed/accel
    'speed': 0.003,  # m/s
    'accel': 0.003,  # m/s²
    # hold_time: 5 # s, default = infinite
}
LIGHTSOURCE = {'name': 'Light Source',
               'role': 'light',
               'port': "/dev/ttyUSB*",
               # source name -> 99% low, 25% low, centre, 25% high, 99% high wavelength in m
               # Values are from vendor: http://lumencor.com/products/filters-for-spectra-x-light-engines/
               'sources': {"UV": [379.e-9, 384.e-9, 390.e-9, 396.e-9, 401.e-9],  # 390/22
                           # 485/25
                           "cyan": [472.e-9, 479.e-9, 485.e-9, 491.e-9, 497.e-9],
                           # 560/32
                           "green": [544.e-9, 552.e-9, 560.e-9, 568.e-9, 576.e-9],
                           # 648/20
                           "red": [638.e-9, 643.e-9, 648.e-9, 653.e-9, 658.e-9],
                           }
               # The light is reflected via a Semrock FF410/504/582/669-DI01-25X36
               }


# This filter-wheel is made so that the light goes through two "holes":
# the filter, and the opposite hole (left empty). So although it has 8
# holes, it only supports 4 filters (from 0° to 135°), and there is no
# "fast-path" between the last filter and the first one.
# positions: {
#    # pos (rad) -> m,m
#     0.08: [510.e-9, 540.e-9], # FF01-440/40-25
#     0.865398: "pass-through", # reflection
#     # 0.865398: [532.e-9, 552.e-9], # FF01-525/30-25
#    1.650796: [589.e-9, 625.e-9], # FF01-607/36-25
#     2.4361944: [672.e-9, 696.e-9], # FF02-684/24-25
# },
# cycle: 6.283185, # position of ref switch (0) after a full turn
# }
#
FILTERWHEEL = {'name': "Filter Wheel",
               'role': 'null',
               'port': "/dev/ttyTMCM*",
               'axes': ["fw"],
               'ustepsize': [1.227184e-6],  # [rad/µstep]
               # rad, more than 0->2 Pi, in order to allow one extra rotation in both direction, when quickly switching
               'address': 7,
               'rng': [[-14, 7]],
               'unit': ["rad"],
               'abs_encoder': None,  # TODO Joes own invention, see if that works
               'refproc': "Standard",
               # digital output used to switch on/off sensor
               'refswitch': {"fw": 0},
               # for the filter wheel, the direction doesn't matter, as long as the positions are correct
               }
