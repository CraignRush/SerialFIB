from odemis.driver.smaract import MCS2



CONFIG_3DOF = {"name": "3DOF",
        "role": "focus",
        "ref_on_init": True,
        "locator": "network:sn:MCS2-00001604",
        # "locator": "fake",
        "speed": 0.003,
        "accel": 0.003,
        #"hold_time": 1.0,
        "axes": {
            'z': {
                'range': [9.e-3, 12.e-3],
                'unit': 'm',
                'channel': 0,
            },
        },
}

testCase=False
if testCase==True:
    CONFIG_3DOF['locator'] = 'fake'
else:
    CONFIG_3DOF['locator'] ='network:sn:MCS2-00003632'
dev = MCS2(**CONFIG_3DOF)


dev.position.value



