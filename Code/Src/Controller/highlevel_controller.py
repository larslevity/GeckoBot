# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 15:51:41 2019

@author: AmP
"""

import time
import logging
import numpy as np
import threading

from Src.Management.thread_communication import llc_ref
from Src.Management.thread_communication import imgproc_rec
from Src.Management.thread_communication import ui_state
from Src.Management import load_pattern as load_ptrn
from Src.Management.thread_communication import sys_config
from Src.Management import state_machine

from Src.Controller import searchtree
from Src.Controller import calibration as clb
from Src.Controller import gait_law_planner
from Src.Controller import KitBasedMotionGenerator as KBMG
from Src.Controller import rotate_on_spot as rotspot


n_pc = len(llc_ref.pressure)
n_dc = len(llc_ref.dvalve)

rootLogger = logging.getLogger()

# Names of Modes
NAMES = {'MODE1': 'PRESSURE',
         'MODE2': 'PATTERN',
         'MODE3': 'GECKO'}

TSAMPLING = .1


class PatternMGMT(object):
    def __init__(self):
        self.last_process_time = time.time()
        self.process_time = 0
        self.initial_cycle = True
        self.pattern = None
        self.version = None
        self.idx = 0
        self.IMAGES = False
        self.init = False
        self.last_fun = [0, 0]

        self.ptrndic = load_ptrn.get_pattern_dic()
        self.default_version = 'vS11' if 'vS11' in self.ptrndic else None
        self.pattern_name = None

    def fun_changed(self, fun, idx):
        if not(fun[idx] == self.last_fun[idx]):
            self.last_fun = fun
            return 1
        return 0

    def select_version(self):
        list_of_keys = [name for name in sorted(iter(self.ptrndic.keys()))]
        self.version = sys_config.UI.select_from_keylist(
                list_of_keys, self.default_version)
        return self.version

    def select_pattern_name(self):
        if self.version:
            list_of_keys = [name for name in sorted(
                    iter(self.ptrndic[mgmt.version].keys()))]
            self.pattern_name = sys_config.UI.select_from_keylist(
                    list_of_keys, self.pattern_name)
        return self.pattern_name


mgmt = PatternMGMT()


class KitBasedMotionGeneratorMGMT(object):
    def __init__(self):
        self.ref_generator = KBMG.ReferenceGenerator()
        self.last_process_time = time.time()
        self.process_time = 0
        self.round = 0
        self.idx = 0


kbmg_mgmt = KitBasedMotionGeneratorMGMT()


class GaitLawMGMT(object):
    def __init__(self):
        self.last_process_time = time.time()
        self.process_time = 0
        self.round = 0


gl_mgmt = GaitLawMGMT()


def mode1():
    sys_config.UI.lcd_display(NAMES['MODE1'])

    while ui_state.mode == 'MODE1':
        switches, potis, fun = ui_state.switches, ui_state.potis, ui_state.fun
        if fun[1]:
            if mgmt.fun_changed(fun, 1):
                sys_config.UI.lcd_display('ANGLE')
            llc_ref.set_state('ANGLE_REFERENCE')
            if not fun[0]:  # pwm = potis*100
                for idx in potis:
                    potis[idx] = potis[idx]*130
                llc_ref.alpha = potis
            else:
                llc_ref.alpha = {idx: 0.0 for idx in range(n_pc)}
        else:  # Pressure Mode
            if mgmt.fun_changed(fun, 1):
                sys_config.UI.lcd_display('PRESSURE')
            llc_ref.set_state('PRESSURE_REFERENCE')
            if not fun[0]:  # ref = potis
                llc_ref.pressure = potis
            else:  # ref = 0
                llc_ref.pressure = {idx: 0.0 for idx in range(n_pc)}
        llc_ref.dvalve = switches
        time.sleep(TSAMPLING)

    return ui_state.mode


def mode2():
    sys_config.UI.lcd_display(NAMES['MODE2'])
    llc_ref.set_state('PRESSURE_REFERENCE')

    # init Pattern mgmt
    if not mgmt.version:
        mgmt.select_version()
#    Always select pattern
    mgmt.select_pattern_name()
    if mgmt.version and mgmt.pattern_name:
        mgmt.pattern = mgmt.ptrndic[mgmt.version][mgmt.pattern_name]

    mgmt.initial_cycle = True

    while ui_state.mode == 'MODE2':
        pattern_ref()
        time.sleep(TSAMPLING)

    return ui_state.mode


def mode3():
    sys_config.UI.lcd_display(NAMES['MODE3'])
    llc_ref.set_state('PRESSURE_REFERENCE')

    choices = list(clb.clb.keys())
    if not mgmt.version:
        mgmt.select_version()
    while mgmt.version not in choices:
        if ui_state.mode != 'MODE3':
            break
        sys_config.UI.lcd_display('selected version\nnot calibrated')
        mgmt.select_version()

    # init
    gl_mgmt.round = 0
    kbmg_mgmt.round, kbmg_mgmt.idx = (0, 0)

    while ui_state.mode == 'MODE3':
        if ui_state.fun[1]:
            KB_MotionGen()
        else:
            optimal_pathplanner()
        time.sleep(TSAMPLING)
    return ui_state.mode


def pattern_ref():
    fun = ui_state.fun
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
            if mgmt.idx % 3 == 2:
                time.sleep(.8)  # hold robot
                fname = time.strftime('%Y-%m-%d--%H-%M-%S', time.localtime())
                sys_config.Camera.make_image(fname)
                time.sleep(.4)  # hold robot

    if fun[1] and not mgmt.IMAGES and sys_config.Camera:
        sys_config.UI.lcd_display('taking photos')
        mgmt.IMAGES = True
        rootLogger.info('RPi takes photos now')
    elif not fun[1] and mgmt.IMAGES and not sys_config.Camera:
        sys_config.UI.lcd_display('stop taking \nphotos')
        mgmt.IMAGES = False
        rootLogger.info('RPi stop to take photos')


def KB_MotionGen():
    fun = ui_state.fun

    if (fun[0] and kbmg_mgmt.last_process_time + kbmg_mgmt.process_time <
            time.time()):

        act_pos = (imgproc_rec.X[1], imgproc_rec.Y[1])
        act_eps = imgproc_rec.eps if imgproc_rec.eps else np.nan
#        xref = imgproc_rec.xref if imgproc_rec.xref[0] else (np.nan, np.nan)
#        XREF = [(0, 0), (20, 30), (-45, 50), (20, 95)]  # cm
        XREF = [(467., 515),  # origin
                (783., 288.),
                (962., 850.),
                (1364., 288.)]
        try:
            xref = XREF[kbmg_mgmt.idx]
            imgproc_rec.xref = xref  # write to recorder
        except IndexError:
            xref = XREF[-1]

        if not np.isnan(xref[0]) and not np.isnan(act_eps):
            # convert measurements
            xbar = gait_law_planner.xbar(xref, act_pos, act_eps)
            xbar = xbar*112./1000  # px to cm
            dist = np.linalg.norm(xbar)
            deps = np.rad2deg(np.arctan2(xbar[1], xbar[0]))
            print('\n\nxbar:\t', [round(x, 2) for x in xbar])
            print('dist:\t', round(dist, 2))
            print('deps:\t', round(deps, 2))

            if dist < 10:
                print('\n\nReached goal ', kbmg_mgmt.idx, ' !!\n\n\n')
                kbmg_mgmt.idx += 1 if kbmg_mgmt.idx < len(XREF) else 0
            else:
                # generate reference
                alpha, foot, ptime, pose_id =  \
                    kbmg_mgmt.ref_generator.get_next_reference(
                        act_pos, act_eps, xref)
                print(pose_id)
                pvtsk, dvtsk = convert_ref(
                        clb.get_pressure(alpha, mgmt.version), foot)
                # send to main thread
                llc_ref.dvalve = dvtsk
                llc_ref.pressure = pvtsk
                # organisation
                kbmg_mgmt.process_time = ptime
                kbmg_mgmt.last_process_time = time.time()


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


def convert_lis2dic(arg):
    out = {}
    for idx, elem in enumerate(arg):
        out[idx] = elem
    return out


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


def optimal_pathplanner():
    fun = ui_state.fun

    if gl_mgmt.round == 0:
        # feasible start pose:
        pvtsk, dvtsk = convert_ref(
                clb.get_pressure([30, 0, -30, 30, 0], mgmt.version),
                [1, 0, 0, 1])
        llc_ref.dvalve = dvtsk
        llc_ref.pressure = pvtsk

    n = 1
    max_step_length = 70
    if (fun[0] and gl_mgmt.last_process_time + gl_mgmt.process_time <
            time.time()):
        # collect measurements
        position = (imgproc_rec.X[1], imgproc_rec.Y[1])
        eps = imgproc_rec.eps if imgproc_rec.eps else np.nan
        xref = imgproc_rec.xref if imgproc_rec.xref[0] else (np.nan, np.nan)
        if not np.isnan(xref[0]) and not np.isnan(eps):
            # convert measurements
            xbar = gait_law_planner.xbar(xref, position, eps)
            xbar = xbar*112./1000  # px to cm
            deps = np.rad2deg(np.arctan2(xbar[1], xbar[0]))
            dist = np.linalg.norm(xbar)

            print('\n\nxbar:\t', [round(x, 2) for x in xbar])
            print('dist:\t', round(dist, 2))
            print('deps:\t', round(deps, 2))

            pressure_ref, feet_act = convert_rec(
                    llc_ref.pressure, llc_ref.dvalve)
            alp_act = clb.get_alpha(pressure_ref, mgmt.version)

            # calc ref
            if abs(deps) > 70:
                pattern = rotspot.rotate_on_spot(deps, alp_act, feet_act)
            else:
                alpha, feet = gait_law_planner.optimal_planner(
                        xbar, alp_act, feet_act, n, max_step_length)
                pattern = [[alp_act, [1, 1, 1, 1], .2],
                           [alp_act, feet, .1],
                           [alpha, feet, 1.5]]
            for idx, pose in enumerate(pattern):
                alpha, feet, ptime = pose
                # convert ref
                pvtsk, dvtsk = convert_ref(
                        clb.get_pressure(alpha, mgmt.version), feet)

                # set ref
                llc_ref.dvalve = dvtsk
                llc_ref.pressure = pvtsk
                if idx != len(pattern)-1:  # last pose -> no sleep
                    time.sleep(ptime)

            print('alpha:\t', [int(a) for a in alpha])
            print('pres:\t', [int(p*100)/100. for p in clb.get_pressure(
                    alpha, mgmt.version)])
#            print('feet:\t', feet)
            print('\n\n---------------------------------\n\n')

            # organisation
            gl_mgmt.process_time = ptime
            gl_mgmt.last_process_time = time.time()
            gl_mgmt.round += 1
        else:
            print('No detection ...')


def exit_cleaner():
    # Clean?
    return ('QUIT')


class HighLevelController(threading.Thread):
    def __init__(self):
        """ """
        threading.Thread.__init__(self)

    def run(self):
        """ run HUI """
        rootLogger.info('Running HIGHLEVEL CTR Thread ...')
        automat = state_machine.StateMachine()
        automat.add_state('MODE1', mode1)
        automat.add_state('MODE2', mode2)
        automat.add_state('MODE3', mode3)
        automat.add_state('EXIT', exit_cleaner)
        automat.add_state('QUIT', None, end_state=True)
        automat.set_start('MODE1')

        try:
            automat.run()
        except Exception as err:
            rootLogger.exception('\n exception HIGHLEVEL CTR Thread \n')
            rootLogger.error(err, exc_info=True)
        rootLogger.info('HIGHLEVEL CTR Thread is done ...')

    def kill(self):
        ui_state.mode = 'EXIT'


# def calc_dist(position, xref):
#    mx, my = position
#    act_pos = np.r_[mx[1], my[1]]
#    dpos = xref - act_pos
#    return np.linalg.norm(dpos)
