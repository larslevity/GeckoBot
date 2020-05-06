# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 14:45:12 2019

@author: AmP
"""

import numpy as np


def rotate_on_spot(deps, alp_act, feet_act, t_fix=.2, t_dfx=.1, t_move=1.5):
    a2 = alp_act[2]
    pattern = []

    # 1. Switch feet
    pattern.append([[45, 45, a2, 45, 45], feet_act, t_fix])
    pattern.append([[45, 45, a2, 45, 45], [1, 1, 1, 1], t_fix])
    if np.sign(a2*deps) < 0:
        feet = [1, 1, 0, 0]
    else:
        feet = [0, 0, 1, 1]
    pattern.append([[45, 45, a2, 45, 45], feet, t_dfx])

    # 2. Swing
    rot = -abs(deps)/2*np.sign(a2)
    pattern.append([[45, 45, rot, 45, 45], feet, t_move])

    # 3. Switch
    pattern.append([[45, 45, rot, 45, 45], [1, 1, 1, 1], t_fix])
    feet = [not(f) for f in feet]
    pattern.append([[45, 45, rot, 45, 45], feet, t_dfx])

    # 4. Swing
    pattern.append([[45, 45, -rot, 45, 45], feet, t_move])

    # 5. Switch
    pattern.append([[45, 45, -rot, 45, 45], [1, 1, 1, 1], t_fix])
    pattern.append([[45, 45, -rot, 45, 45], feet_act, t_fix])

    return pattern
