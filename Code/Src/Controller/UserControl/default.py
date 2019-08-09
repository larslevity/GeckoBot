# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 15:51:41 2019

@author: AmP
"""

import time
import logging
import numpy as np

from Src.Management.thread_communication import llc_ref
from Src.Management.thread_communication import imgproc_rec
from Src.Management import load_pattern as load_ptrn
from Src.Hardware import lcd as lcd_module
from Src.Management.thread_communication import sys_config

from Src.Controller import searchtree
from Src.Controller import calibration as clb
from Src.Controller import gait_law_planner


n_pc = len(llc_ref.pressure)
n_dc = len(llc_ref.dvalve)

lcd = lcd_module.getlcd()
rootLogger = logging.getLogger()

# Names of Modes
NAMES = ['PRESSURE / PWM', 'PATTERN', 'GECKO']


class PatternMGMT(object):
    def __init__(self):
        self.last_process_time = time.time()
        self.process_time = 0
        self.initial_cycle = True
        self.pattern = None
        self.idx = 0
        self.IMAGES = False
        self.init = False

        self.ptrndic = load_ptrn.get_pattern_dic()
        self.default_version = 'vS11' if 'vS11' in self.ptrndic else None
        self.default_pattern = None


mgmt = PatternMGMT()


class SearchTreeMGMT(object):
    def __init__(self):
        self.ref_generator = searchtree.ReferenceGenerator()
        self.last_process_time = time.time()
        self.process_time = 0

        self.version = None
        self.init = False


st_mgmt = SearchTreeMGMT()


class GaitLawMGMT(object):
    def __init__(self):
        self.last_process_time = time.time()
        self.process_time = 0

        self.version = None
        self.init = False
        self.round = 0


gl_mgmt = GaitLawMGMT()



def mode1(switches, potis, fun):
    mgmt.initial_cycle = True
    mgmt.init = False
    st_mgmt.init = False

    if fun[1]:  # PWM Mode
        llc_ref.set_state('FEED_THROUGH')
        if not fun[0]:  # pwm = potis*100
            for idx in potis:
                potis[idx] = potis[idx]*100
            llc_ref.pwm = potis
        else:  # pwm = 0
            llc_ref.pwm = {idx: 0.0 for idx in range(n_pc)}
    else:  # Pressure Mode
        llc_ref.set_state('PRESSURE_REFERENCE')
        if not fun[0]:  # ref = potis
            llc_ref.pressure = potis
        else:  # ref = 0
            llc_ref.pressure = {idx: 0.0 for idx in range(n_pc)}
    llc_ref.dvalve = switches


def mode2(switches, potis, fun):
    llc_ref.set_state('PRESSURE_REFERENCE')
    pattern_ref(fun)


def mode3(switches, potis, fun):
    llc_ref.set_state('PRESSURE_REFERENCE')
    if fun[1]:
        searchtree_pathplanner(fun)
    else:
        optimal_pathplanner(fun)


def pattern_ref(fun):
    if not mgmt.init:  # Ask which version
        mgmt.default_version = lcd.select_from_dic(
                mgmt.ptrndic, mgmt.default_version)
        mgmt.default_pattern = lcd.select_from_dic(
                mgmt.ptrndic[mgmt.default_version], mgmt.default_pattern)
        mgmt.pattern = mgmt.ptrndic[mgmt.default_version][mgmt.default_pattern]
        mgmt.init = True

    if (fun[0] and mgmt.last_process_time + mgmt.process_time < time.time()):
        if mgmt.initial_cycle:  # initial cycle
            pattern = get_initial_pose(mgmt.pattern)
            mgmt.idx = 0
            mgmt.initial_cycle = False
        else:  # normaler style
            pattern = mgmt.pattern

        # generate tasks
        dvtsk, pvtsk, processtime = generate_pose_ref(pattern, mgmt.idx)
        # send to main thread
        llc_ref.dvalve = dvtsk
        llc_ref.pressure = pvtsk
        # organisation
        mgmt.process_time = processtime
        mgmt.last_process_time = time.time()
        mgmt.idx = mgmt.idx+1 if mgmt.idx < len(pattern)-1 else 0
        # capture image?
        if sys_config.Camera and mgmt.IMAGES:
            if mgmt.idx % 3 == 1:
                fname = time.strftime('%Y-%m-%d--%H-%M-%S', time.localtime())
                sys_config.Camera.make_image(fname)

    if fun[1] and not mgmt.IMAGES and sys_config.Camera:
        mgmt.IMAGES = True
        rootLogger.info('RPi takes photos now')
    elif not fun[1] and mgmt.IMAGES and not sys_config.Camera:
        mgmt.IMAGES = False
        rootLogger.info('RPi stop to take photos')


def searchtree_pathplanner(fun):
    if not st_mgmt.init:  # first select version
        choice = list(clb.clb.keys())
        std = 'vS11' if 'vS11' in choice else None
        st_mgmt.version = lcd.select_elem_from_list(choice, std, 'Version?')
        st_mgmt.init = True

    if (fun[0] and st_mgmt.last_process_time + st_mgmt.process_time <
            time.time()):
        xref = imgproc_rec.xref
        act_eps = imgproc_rec.eps

        if xref[0] and act_eps:
            act_pos = (imgproc_rec.X[1], imgproc_rec.Y[1])

            # generate reference
            alpha, foot, ptime, pose_id =  \
                st_mgmt.ref_generator.get_next_reference(
                    act_pos, act_eps, xref)
            print(pose_id)
            pvtsk, dvtsk = convert_ref(
                    clb.get_pressure(alpha, st_mgmt.version), foot)
            # send to main thread
            llc_ref.dvalve = dvtsk
            llc_ref.pressure = pvtsk
            # organisation
            st_mgmt.process_time = ptime
            st_mgmt.last_process_time = time.time()


def get_initial_pose(pattern, hold0=5., hold1=1.):
    ref0 = pattern[0]
    ref0 = ref0[:8] + [False]*4 + [hold0]
    ref1 = ref0[:8] + [False, True, True, False] + [hold1]
    return [ref0, ref1]


def convert_ref(pressure, foot):
    dv_task, pv_task = {}, {}
    for jdx, dp in enumerate(foot):
        dv_task[jdx] = dp
    for kdx, pp in enumerate(pressure):
        pv_task[kdx] = pp

    return pv_task, dv_task


def convert_rec(pv_task, dv_task):
    pressure, foot = [], []
    for key in dv_task:
        foot.append(dv_task[key])
    for key in pv_task:
        pressure.append(pv_task[key])
    return pressure, foot


def generate_pose_ref(pattern, idx):
    pos = pattern[idx]
    dv_task, pv_task = {}, {}

    local_min_process_time = pos[-1]
    dpos = pos[-n_dc-1:-1]
    ppos = pos[:n_pc]
    for jdx, dp in enumerate(dpos):
        dv_task[jdx] = dp
    for kdx, pp in enumerate(ppos):
        pv_task[kdx] = pp

    return dv_task, pv_task, local_min_process_time


def optimal_pathplanner(fun):
    if not gl_mgmt.init:  # first select version
        choice = list(clb.clb.keys())
        std = 'vS11' if 'vS11' in choice else None
        gl_mgmt.version = lcd.select_elem_from_list(choice, std, 'Version?')
        gl_mgmt.init = True

    if not fun[0]:
        gl_mgmt.round = 0

    if gl_mgmt.round == 0:
        print('Set start Pose')
        # feasible start pose:
        pvtsk, dvtsk = convert_ref(
                clb.get_pressure([30, 0, -30, 30, 0], gl_mgmt.version),
                [1, 0, 0, 1])
        llc_ref.dvalve = dvtsk
        llc_ref.pressure = pvtsk

    n = 1
    if (fun[0] and gl_mgmt.last_process_time + gl_mgmt.process_time <
            time.time()):
        # collect measurements
        position = (imgproc_rec.X[1], imgproc_rec.Y[1])
        eps = imgproc_rec.eps
        xref = imgproc_rec.xref
        if xref[0] and position[0] and eps:
            # convert measurements
            xbar = gait_law_planner.xbar(xref, position, eps)
            xbar = xbar/30
            deps = np.rad2deg(np.arctan2(xbar[1], xbar[0]))

            print('\n\nxbar:\t', [round(x,2) for x in xbar])
            print('deps:\t', round(deps,2))

            pressure_ref, feet = convert_rec(llc_ref.pressure, llc_ref.dvalve)
            alp_act = clb.get_alpha(pressure_ref, gl_mgmt.version)
            # calc ref
            alpha, feet = gait_law_planner.optimal_planner(
                    xbar, alp_act, feet, n)
            # convert ref
            pvtsk, dvtsk = convert_ref(
                    clb.get_pressure(alpha, gl_mgmt.version), feet)

            print('alpha:\t', [round(a,2) for a in alpha])
            print('pres:\t', [round(p,2) for p in clb.get_pressure(alpha, gl_mgmt.version)])
            print('feet:\t', feet)

            # switch feet
            llc_ref.dvalve = {idx: True for idx in range(4)}
            time.sleep(.3)
            llc_ref.dvalve = dvtsk
            time.sleep(.1)
            # set ref
            llc_ref.pressure = pvtsk
            # organisation
            ptime = 1.5
            gl_mgmt.process_time = ptime
            gl_mgmt.last_process_time = time.time()
            gl_mgmt.round += 1


#def calc_dist(position, xref):
#    mx, my = position
#    act_pos = np.r_[mx[1], my[1]]
#    dpos = xref - act_pos
#    return np.linalg.norm(dpos)
