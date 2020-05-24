#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 24 17:01:43 2020

@author: ls
"""
import numpy as np
from Src.Controller import gait_law_planner



class Oscillator(object):
    def __init__(self, alp=[10, 10, 10, 10, 10], feet=[1, 0, 0, 1]):
        self.last_alp = alp
        self.last_feet = feet

    def set_state(self, alp, feet):
        self.last_alp = alp
        self.last_feet = feet


    def get_ref(self, q1, q2, t=[1.2, .1, .1]):
        """
        1. generate reference according to input
        2. Check fixation
            a. fix
            b. defix
        3. move
        """
        pattern = []
        sign = np.sign(self.last_alp[2]) if self.last_alp[2] != 0 else 1
        alp = gait_law_planner.alpha(abs(q1)*sign*(-1), q2)
        feet = [0, 1, 1, 0] if alp[2] > 0 else [1, 0, 0, 1]  # ><
        if q1 < 0:  # switch fix for running backwards
            feet = [not(foot) for foot in feet]
        if feet != self.last_feet:  # switch fix
            pattern.append([self.last_alp, [1, 1, 1, 1], t[1]])  # fix
            pattern.append([self.last_alp, feet, t[2]])  # defix
        pattern.append([alp, feet, t[0]])  # move

        self.last_alp = alp
        self.last_feet = feet
        
        return pattern