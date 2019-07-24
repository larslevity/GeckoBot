# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 12:29:50 2019

@author: AmP
"""


## CHANNELS


MAX_PRESSURE = 1.   # bar
MAX_CTROUT = 0.50     # [10V]
TSAMPLING = 0.001     # [sec]
PID = [1.05, 0.03, 0.01]    # [1]
PIDimu = [0.0117, 1.012, 0.31]

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
    0: {'PSensid': 4, 'pin': 'P9_22', 'ctr': PID, 'IMUs': [0, 1], 'IMUrot': -90, 'ctrIMU': PIDimu},
    1: {'PSensid': 5, 'pin': 'P8_19', 'ctr': PID, 'IMUs': [1, 2], 'IMUrot': -90, 'ctrIMU': PIDimu},
    2: {'PSensid': 2, 'pin': 'P9_21', 'ctr': PID, 'IMUs': [1, 4], 'IMUrot': 180, 'ctrIMU': PIDimu},
    3: {'PSensid': 3, 'pin': 'P8_13', 'ctr': PID, 'IMUs': [4, 1], 'IMUrot': 180, 'ctrIMU': PIDimu},
    4: {'PSensid': 0, 'pin': 'P9_14', 'ctr': PID, 'IMUs': [4, 3], 'IMUrot': -90, 'ctrIMU': PIDimu},
    5: {'PSensid': 1, 'pin': 'P9_16', 'ctr': PID, 'IMUs': [5, 4], 'IMUrot': -90, 'ctrIMU': PIDimu},
    6: {'PSensid': 7, 'pin': 'P9_28', 'ctr': PID, 'IMUs': [None], 'IMUrot': None, 'ctrIMU': None},
#    7: {'PSensid': 6, 'pin': 'P9_42', 'ctr': PID, 'IMUs': [None], 'IMUrot': None, 'ctrIMU': None}
    }
DiscreteCHANNELset = {
    0: {'pin': 'P8_10'},
    1: {'pin': 'P8_7'},
    2: {'pin': 'P8_8'},
    3: {'pin': 'P8_9'}
    }