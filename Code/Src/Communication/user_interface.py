# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 15:45:16 2018

@author: Lars Schiller
"""

from __future__ import print_function

# import __builtin__
import threading
import time
import sys
import Adafruit_BBIO.GPIO as GPIO
import errno
from socket import error as SocketError


from Src.Management import state_machine
from Src.Visual.GUI import datamanagement as mgmt

UI_TSAMPLING = .1

MODE1 = "P9_23"
MODE2 = "P9_27"
MODE3 = 'P9_30'  # "P9_25" doesnt work.
FUN1 = "P9_24"
FUN2 = "P9_26"
BTNS = [MODE1, MODE2, MODE3, FUN1, FUN2]

MODE = {
    1: {'ui_state': 'PWM_FEED_THROUGH',
        'main_state': 'FEED_THROUGH',
        'pin': MODE1},
    2: {'ui_state': 'USER_REFERENCE',
        'main_state': {0: 'PRESSURE_REFERENCE', 1: 'ANGLE_REFERENCE'},
        'pin': MODE2},
    3: {'ui_state': 'PATTERN_REFERENCE',
        'main_state': {0: 'PRESSURE_REFERENCE', 1: 'ANGLE_REFERENCE'},
        'pin': MODE3}
    }

MODE1LED = "P8_15"
MODE2LED = "P8_14"
MODE3LED = "P8_17"
FUN1LED = "P8_16"
FUN2LED = "P8_18"
LEDS = [MODE1LED, MODE2LED, MODE3LED, FUN1LED, FUN2LED]

SWITCHES = {0: "P9_11", 1: "P9_17", 2: "P9_15", 3: "P9_13"}
POTIS = {0: "P9_40", 1: "P9_38", 2: "P9_33", 3: "P9_39",
         4: "P9_36", 5: "P9_35", 6: "P9_37", 7: "P9_37"}


def flicker_leds():
    for i in range(3):
        for led in LEDS:
            GPIO.output(led, GPIO.HIGH)
        time.sleep(.05)
        for led in LEDS:
            GPIO.output(led, GPIO.LOW)
        time.sleep(.05)


def ring_leds():
    for i in range(5):
        for led in LEDS:
            GPIO.output(led, GPIO.HIGH)
            time.sleep(.05)
            GPIO.output(led, GPIO.LOW)
        time.sleep(.05)


def generate_pattern(p0, p1, p2, p3, p4, p5, p6, p7, t_move=3.0, t_fix=.66,
                     t_dfx=.25, stiffener=True):
    p01, p11, p41, p51 = [.25]*4 if stiffener else [.0]*4

    data = [
        [p01, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, False, t_move],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, False, False, True, t_dfx],
        [p0, p11, 0.0, p3, p4, p51, 0.0, p7, True, False, False, True, t_move],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, False, True, True, False, t_dfx]
    ]
    return data


def get_initial_pose(pattern, hold0=5., hold1=1.):
    ref0 = pattern[0]
    ref0 = ref0[:8] + [False]*4 + [hold0]
    ref1 = ref0[:8] + [False, True, True, False] + [hold1]
    return [ref0, ref1]


class HUIThread(threading.Thread):
    def __init__(self, shared_memory, rootLogger=None, camerasock=None):
        """ """
        threading.Thread.__init__(self)
        self.shared_memory = shared_memory

        self.ui_state = 'PATTERN_REFERENCE'

        self.lastfun1 = time.time()
        self.lastfun2 = time.time()
        self.lastchange = time.time()
        self.fun1 = False
        self.fun2 = False

        self.user_pattern = False  # user defined pattern or default?
        self.ptrn_idx = 0
        self.last_process_time = time.time()
        self.process_time = 0

        self.rootLogger = rootLogger
        self.rootLogger.info('Initialize HUI Thread ...')

        self.camerasock = camerasock
        self.camidx = 0

        for btn in BTNS:
            GPIO.setup(btn, GPIO.IN)
            GPIO.add_event_detect(btn, GPIO.RISING)
        for led in LEDS:
            GPIO.setup(led, GPIO.OUT)
        for idx in SWITCHES:
            GPIO.setup(SWITCHES[idx], GPIO.IN)
        ring_leds()

    def set_camera_socket(self, socket):
        self.camerasock = socket

    def run(self):
        """ run HUI """
        self.rootLogger.info('Running HUI Thread ...')

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- HELP FUNCTIONS    ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        def change_state_in_main_thread(state):
            self.shared_memory.task_state_of_mainthread = state

        def mode_changed():
            new_state = None
            if self.ui_state == 'EXIT':
                new_state = 'EXIT'

            change = False
            if new_state and time.time()-self.lastchange > 1:
                change = True
                self.ui_state = new_state
                self.rootLogger.info("UI goes to: {}".format(new_state))
                self.lastchange = time.time()

            return change

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- STATE HANDLERS    ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        def exit_cleaner():
            change_state_in_main_thread('EXIT')
            return ('QUIT')

        def pause_state():
            while not mode_changed():
                time.sleep(UI_TSAMPLING)
            return (self.ui_state)

        def pattern_reference():

            act_is_connected = {}
            act_is_connected[0] = True
            act_is_connected[1] = True

            def check_actuator(n_cycles):
                for idx in range(2):
                    if act_is_connected[idx]:
                        if self.shared_memory.rec[idx] > 0:
                            if self.shared_memory.rec_angle[idx] < 40:
                                act_is_connected[idx] = False
                                print('Actuator ', idx, 'destroyed. Number of cycles: ', (n_cycles-1)/3)

            self.ptrn_idx = 0
            n_cycles = 0
            while not mode_changed():
                change_state_in_main_thread(MODE[3]['main_state'][0])
                if (self.last_process_time + self.process_time < time.time()):
                    pattern = self.shared_memory.pattern
                    idx = self.ptrn_idx
                    self.ptrn_idx = idx+1 if idx < len(pattern)-1 else 0
                    # capture image?
                    if self.camerasock:  # not video but image
                        if act_is_connected[0] or act_is_connected[1]:
                            if n_cycles % 1500 == 1:
                                self.camerasock.make_image(
                                        'test'+str(self.camidx))
                                self.camidx += 1
                    # generate tasks
                    dvtsk, pvtsk, processtime = generate_pose_ref(pattern, idx)
                    # check if act is bursted:
                    if idx == 1:
                        check_actuator(n_cycles)
                    for idx in range(2):
                        if not act_is_connected[idx]:
                            pvtsk[idx] = 0
                    # send to main thread
                    self.shared_memory.dvalve_task = dvtsk
                    self.shared_memory.ref_task = pvtsk
                    # organisation
                    self.process_time = processtime
                    self.last_process_time = time.time()

                    n_cycles += 1

                    if not (act_is_connected[0] or act_is_connected[1]):
                        change_state_in_main_thread('EXIT')
                        self.ui_state = 'EXIT'

                time.sleep(UI_TSAMPLING)
            return (self.ui_state)

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- RUN STATE MACHINE ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        automat = state_machine.StateMachine()
        automat.add_state('PAUSE', pause_state)
        automat.add_state('PATTERN_REFERENCE', pattern_reference)
        automat.add_state('EXIT', exit_cleaner)
        automat.add_state('QUIT', None, end_state=True)
        automat.set_start('PATTERN_REFERENCE')

        try:
            automat.run()
        except Exception as err:
            self.rootLogger.exception('\n exception HUI Thread \n')
            self.rootLogger.exception(
                    "Unexpected error:\n", sys.exc_info()[0])
            self.rootLogger.exception(sys.exc_info()[1])
            self.rootLogger.error(err, exc_info=True)

            self.rootLogger.info('Exit the HUI Thread ...')
            change_state_in_main_thread('EXIT')

        self.rootLogger.info('HUI Thread is done ...')

    def kill(self):
        self.ui_state = 'EXIT'


n_dvalves = 0
n_pvalves = 2


def generate_pose_ref(pattern, idx):
    pos = pattern[idx]
    dv_task, pv_task = {}, {}

    local_min_process_time = pos[-1]
    dpos = pos[-n_dvalves-1:-1]
    ppos = pos[:n_pvalves]
    for jdx, dp in enumerate(dpos):
        dv_task[jdx] = dp
    for kdx, pp in enumerate(ppos):
        pv_task[kdx] = pp

    return dv_task, pv_task, local_min_process_time


class Printer(threading.Thread):
    def __init__(self, shared_memory, imgprocsock=None, plotsock=None,
                 IMU=False):
        threading.Thread.__init__(self)
        self.shared_memory = shared_memory
        self.state = 'RUN'
        self.imgprocsock = imgprocsock
        self.plotsock = plotsock
        self.IMU_connected = True if IMU else False

    def prepare_data(self):
        p = [round(self.shared_memory.rec[i], 2) for i in range(2)]
        r = [round(self.shared_memory.ref_task[i], 2) for i in range(2)]
        u = [round(self.shared_memory.rec_u[i], 2) for i in range(2)]

        if self.imgprocsock:
            alpha = self.imgprocsock.get_alpha()
            alpha = alpha + [None]*(2 - len(alpha))
            aIMU = [round(alpha[i], 2) if alpha[i] else None for i in range(2)]
            for i in range(2):
                self.shared_memory.rec_angle[i] = alpha[i]
            IMU = True

        return (p, r, u, aIMU, IMU)

    def print_state(self):
        if self.imgprocsock:
            alpha = self.imgprocsock.get_alpha()
            alpha = alpha + [None]*(8 - len(alpha))
            alpha = [
                round(alpha[i], 2) if alpha[i] else None for i in range(8)]
            for i in range(8):
                self.shared_memory.rec_angle[i] = alpha[i]
            X = [None]*8
            Y = [None]*8
            eps = [None]*4
        else:
            alpha, X, Y, eps = [None]*8, [None]*8, [None]*8, [None]*4
        state_str = (
             '\n\t| Ref \t| p \t| PWM \t| aIMU \t| aIMG \t| POS  \n')
        state_str = state_str + '-'*75 + '\n'
        for i in range(2):
            rec_angle = self.shared_memory.rec_angle
            angle = round(rec_angle[i], 2) if rec_angle[i] else None
            angle_imgProc = round(alpha[i], 2) if alpha[i] else None
            x = round(X[i], 1) if X[i] else None
            y = round(Y[i], 1) if Y[i] else None
            s = '{}\t| {}\t| {}\t| {}\t| {}\t| {}\t| ({},{})\n'.format(
                i, self.shared_memory.ref_task[i],
                round(self.shared_memory.rec[i], 2),
                round(self.shared_memory.rec_u[i], 2), angle,
                angle_imgProc, x, y)
            state_str = state_str + s
        print(state_str)

    def run(self):
        while self.state != 'EXIT':
            if self.plotsock:
                try:
                    sample = mgmt.rehash_record(*self.prepare_data())
                    _ = self.plotsock.send_sample(sample)
                except SocketError as err:
                    if err.errno != errno.ECONNRESET:
                        raise
                    print(err)
                    self.plotsock = None

            else:
                self.print_state()
                time.sleep(.1)

    def kill(self):
        self.state = 'EXIT'
