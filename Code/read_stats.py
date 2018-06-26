# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 12:34:46 2018

@author: AmP

Profiler stats.
"""

import pstats

p = pstats.Stats('log.txt')
p.strip_dirs().sort_stats('tottime').print_stats()