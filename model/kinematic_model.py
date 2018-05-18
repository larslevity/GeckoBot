# -*- coding: utf-8 -*-
"""
Created on Fri May 18 16:11:13 2018

@author: AmP
"""

import matplotlib.pyplot as plt


class RobotRepr(object):
    def __init__(self):
        self.len_leg = 1
        self.len_tor = 1.4
        self.state = {'alp1': 0, 'alp2': 0, 'gam': 0, 'bet1': 0, 'bet2': 0,
                      'f1': True, 'f2': False, 'f3': False, 'f4': False}
        self.coords = {'F1': (0, 0), 'F2': (2*self.len_leg, 0),
                       'F3': (0, -self.len_tor),
                       'F4': (2*self.len_leg, -self.len_tor)}

    def get_repr(self):
        