#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 09:12:58 2018

@author: bianca

Refeference Generator
"""


n_dvalves = 4
n_pvalves = 8


def generate_walking_ref(pattern, idx):
    pos = pattern[idx]
    dv_task, pv_task = {}, {}

    local_min_process_time = pos[-1]
    dpos = pos[-n_dvalves-1:-1]
    ppos = pos[:n_pvalves]
    for jdx, dp in enumerate(dpos):
        dv_task[str(jdx)] = dp
    for kdx, pp in enumerate(ppos):
        pv_task[str(kdx)] = pp
#    time.sleep(local_min_process_time)

    return dv_task, pv_task, local_min_process_time

