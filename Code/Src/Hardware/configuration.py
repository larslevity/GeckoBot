# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 12:29:50 2019

@author: AmP
"""

# CHANNELS

MAX_CTROUT = 0.50     # [10V]
MAX_PRESSURE_REF = 1.1
TSAMPLING = 0.001     # [sec]
PID = [0.0117, 1.012, 0.31]    # [1]

STARTSTATE = 'PAUSE'


'''
Positions of IMUs:
<       ^       >
0 ----- 1 ----- 2
        |
        |
        |
3 ------4 ------5
<       v       >
In IMUcalc.calc_angle(acc0, acc1, rot_angle), "acc0" is turned by rot_angle
'''

IMUset = {
    0: {'id': 0},
    1: {'id': 1},
    2: {'id': 2},
    3: {'id': 3},
    4: {'id': 4},
    5: {'id': 5}
    }

CHANNELset = {
    0: {'pin': 'P9_22', 'ctr': PID, 'IMUs': [0, 1], 'IMUrot': -90},
    1: {'pin': 'P9_14', 'ctr': PID, 'IMUs': [1, 2], 'IMUrot': -90},
    2: {'pin': 'P8_13', 'ctr': PID, 'IMUs': [1, 4], 'IMUrot': 180},
    3: {'pin': 'P9_16', 'ctr': PID, 'IMUs': [4, 1], 'IMUrot': 180},
    4: {'pin': 'P8_19', 'ctr': PID, 'IMUs': [4, 3], 'IMUrot': -90},
    5: {'pin': 'P9_21', 'ctr': PID, 'IMUs': [5, 4], 'IMUrot': -90},
    }

DiscreteCHANNELset = {
    0: {'pin': 'P8_10'},
    1: {'pin': 'P8_7'},
    2: {'pin': 'P8_8'},
    3: {'pin': 'P8_9'}
    }
