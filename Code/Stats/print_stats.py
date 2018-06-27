#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:39:27 2018

@author: bianca
"""


import pstats

#stat = 'imu-ref-fast-mode.pstats'
stat = 'pressure-ref-fast-mode.pstats'

order = 'tottime'
#order = 'cumtime'

p = pstats.Stats(stat)
p.strip_dirs().sort_stats(order).print_stats(45)