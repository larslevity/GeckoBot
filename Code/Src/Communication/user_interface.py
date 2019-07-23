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
import Adafruit_BBIO.ADC as ADC
import errno
from socket import error as SocketError

# lcd stuff ...
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as char_lcd

from Src.Management import state_machine
from Src.Visual.GUI import datamanagement as mgmt
from Src.Controller import reference as ref_gen
from Src.Controller import calibration as clb

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
    3: {'ui_state': 'APRILTAG_REFERENCE',
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


def all_potis_zero():
    zero = False
    potis = read_potis().values()
    if sum(potis) == 0:
        zero = True
    return zero


def read_potis():
    potis = {}
    for idx in POTIS:
        val = ADC.read(POTIS[idx])  # bug-> read twice
        val = round(ADC.read(POTIS[idx])*100)/100
        potis[idx] = val
    return potis


def read_switches():
    switches = {}
    for idx in SWITCHES:
        switches[idx] = True if GPIO.input(SWITCHES[idx]) else False
    return switches


# def print(*args, **kwargs):
#    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


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


def init_lcd_display():
    cols = 16
    rows = 2
    i2c = busio.I2C(board.SCL, board.SDA)
    lcd = char_lcd.Character_LCD_RGB_I2C(i2c, cols, rows)
    lcd.color = [100, 0, 0]
    lcd.message = 'Display initialized!'
    return lcd


class HUIThread(threading.Thread):
    def __init__(self, shared_memory, rootLogger=None, camerasock=None):
        """ """
        threading.Thread.__init__(self)
        self.shared_memory = shared_memory

        self.ui_state = 'PAUSE'

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

        self.rootLogger.info('Initialize LCD Display ...')
        self.lcd = init_lcd_display()

        ADC.setup()

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
#            while not self.shared_memory.actual_state_of_mainthread == state:
#                time.sleep(self.shared_memory.sampling_time)

        def mode_changed():
            new_state = None
            if GPIO.event_detected(MODE1):
                new_state = MODE[1]['ui_state']
            elif GPIO.event_detected(MODE2):
                new_state = MODE[2]['ui_state']
            elif GPIO.event_detected(MODE3):
                new_state = MODE[3]['ui_state']
            elif self.ui_state == 'EXIT':
                new_state = 'EXIT'

            change = False
            if new_state and time.time()-self.lastchange > 1:
                if (all_potis_zero() and new_state is not self.ui_state
                        or new_state == 'EXIT'):
                    change = True
                    self.ui_state = new_state
                    self.rootLogger.info("UI goes to: {}".format(new_state))
                    reset_events()
                    self.lastchange = time.time()
                    self.lcd.message = new_state + 'SELECTED'
                else:
                    flicker_leds()
                    self.lcd.message = 'Potis not zero ...'
            return change

        def fun1():
            if GPIO.event_detected(FUN1):
                if time.time()-self.lastfun1 > 1:
                    state = self.fun1
                    self.fun1 = not state
                    self.rootLogger.info('Fun1 turned {}'.format(not state))
                    self.lastfun1 = time.time()
            return self.fun1

        def fun2():
            if GPIO.event_detected(FUN2):
                if time.time()-self.lastfun2 > 1:
                    state = self.fun2
                    self.fun2 = not state
                    self.rootLogger.info('Fun2 turned {}'.format(not state))
                    self.lastfun2 = time.time()
            return self.fun2

        def is_userpattern():
            if all_potis_zero():
                if self.user_pattern:
                    self.user_pattern = False
                    self.shared_memory.pattern = \
                        self.shared_memory.ptrndic[
                                self.shared_memory.ptrndic['selected']]
                    self.rootLogger.info('user_pattern was turned False')
            else:
                if not self.user_pattern:
                    self.user_pattern = True
                    self.rootLogger.info('user_pattern was turned True')
            return self.user_pattern

        def reset_events():
            for btn in BTNS:
                GPIO.event_detected(btn)
            self.fun1 = False
            self.fun2 = False

        def set_leds():
            my_state = self.ui_state
            for pin, state in [(MODE1LED, MODE[1]['ui_state']),
                               (MODE2LED, MODE[2]['ui_state']),
                               (MODE3LED, MODE[3]['ui_state'])]:
                GPIO.output(pin, GPIO.HIGH if my_state == state else GPIO.LOW)
            for pin, state in [(FUN1LED, self.fun1),
                               (FUN2LED, self.fun2)]:
                GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

        def select_pattern():
            patterns = [
                name for name in sorted(
                        iter(self.shared_memory.ptrndic.keys()))]
            patterns.remove('selected')
            current_selection = self.shared_memory.ptrndic['selected']
            select = None
            idx = patterns.index(current_selection)
            self.lcd.message = patterns[idx]
            while not mode_changed() and select is None:
                if self.lcd.up_button:
                    idx = idx - 1 if idx > 0 else len(patterns) - 1
                    self.lcd.clear()
                    self.lcd.message = patterns[idx]
                elif self.lcd.down_button:
                    idx = idx + 1 if idx < len(patterns) - 1 else 0
                    self.lcd.clear()
                    self.lcd.message = patterns[idx]
                elif self.lcd.select_button or fun1():
                    self.lcd.clear()
                    self.lcd.message = "SELECTED"
                    select = patterns[idx]
                    self.shared_memory.ptrndic['selected'] = patterns[idx]
                time.sleep(.2)

            self.lcd.clear()

            if select:
                return self.shared_memory.ptrndic[
                        self.shared_memory.ptrndic['selected']]
            else:
                return None

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- STATE HANDLERS    ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        def exit_cleaner():
            change_state_in_main_thread('EXIT')
            return ('QUIT')

        def pause_state():
            while not mode_changed():
                time.sleep(UI_TSAMPLING)
                set_leds()
            return (self.ui_state)

        def pwm_feed_through():
            self.lcd.message = 'PWM FEED THROUGH MODE'
            change_state_in_main_thread(MODE[1]['main_state'])
            while not mode_changed():
                cref = read_potis()
                for idx in self.shared_memory.pwm_task:
                    self.shared_memory.pwm_task[idx] = cref[idx]*100

                dref = read_switches()
                for idx in self.shared_memory.dvalve_task:
                    self.shared_memory.dvalve_task[idx] = dref[idx]
                time.sleep(UI_TSAMPLING)
                set_leds()
            return (self.ui_state)

        def user_reference():
            self.lcd.message = \
                'PRESSURE REFERENCE MODE\nBtn1 -> ref=0, Btn2 -> AngleRef'
            while not mode_changed():
                change_state_in_main_thread(MODE[2]['main_state'][fun2()])
                refzero = fun1()
                cref = (read_potis() if not refzero else
                        {idx: 0.0 for idx in self.shared_memory.ref_task})
                for idx in self.shared_memory.ref_task:
                    self.shared_memory.ref_task[idx] = cref[idx]

                dref = read_switches()
                for idx in self.shared_memory.dvalve_task:
                    self.shared_memory.dvalve_task[idx] = dref[idx]

                time.sleep(UI_TSAMPLING)
                set_leds()
            return (self.ui_state)

        def pattern_reference():
            IMAGES = False
            # first select pattern
            set_leds()
            pattern = select_pattern()
            if pattern:
                self.shared_memory.pattern = pattern
            # always start with ref0
            self.ptrn_idx = 0
            initial_cycle, initial_cycle_idx = True, 0
            while not mode_changed():
                self.lcd.message = \
                    'PATTERN REFERENCE MODE\nBtn1 -> Start, Btn2 -> IMAGES'
                change_state_in_main_thread(MODE[3]['main_state'][0])
                if is_userpattern():
                    cref = read_potis().values()
                    self.shared_memory.pattern = generate_pattern(*cref)
                if (fun1() and self.last_process_time + self.process_time <
                        time.time()):
                    if initial_cycle:  # initial cycle
                        pattern = get_initial_pose(self.shared_memory.pattern)
                        idx = initial_cycle_idx
                        initial_cycle_idx += 1
                        if initial_cycle_idx > 1:
                            initial_cycle = False
                    else:  # normaler style
                        pattern = self.shared_memory.pattern
                        idx = self.ptrn_idx
                        self.ptrn_idx = idx+1 if idx < len(pattern)-1 else 0
                    # generate tasks
                    dvtsk, pvtsk, processtime = generate_pose_ref(pattern, idx)
                    # send to main thread
                    self.shared_memory.dvalve_task = dvtsk
                    self.shared_memory.ref_task = pvtsk
                    # organisation
                    self.process_time = processtime
                    self.last_process_time = time.time()
                    # capture image?
                    if self.camerasock and IMAGES:
                        if idx % 3 == 1:
                            self.camerasock.make_image('img'+str(self.camidx))
                            self.camidx += 1

                if fun2() and not IMAGES:
                    IMAGES = True
                    self.lcd.message = 'RPi takes photos now'
                elif not fun2() and IMAGES:
                    IMAGES = False
                    self.lcd.message = 'RPi stop to take photos'

                time.sleep(UI_TSAMPLING)
                set_leds()
            return (self.ui_state)

        def apriltag_reference():
            # first select version
            set_leds()
            version = select_pattern()[0][0]
#            print(version)
            ref_generator = ref_gen.ReferenceGenerator()
#            dvtsk, pvtsk = convert_ref(
#                    clb.get_pressure([0, 0, 0, 0, 0], version), [0, 0, 0, 0])
#            print(dvtsk)
#            print(pvtsk)
#            # send to main thread
#            self.shared_memory.dvalve_task = dvtsk
#            self.shared_memory.ref_task = pvtsk

            while not mode_changed():
                change_state_in_main_thread(MODE[3]['main_state'][fun2()])

                if (fun1() and self.last_process_time + self.process_time <
                        time.time()):
                    xref = self.shared_memory.xref
                    act_eps = self.shared_memory.rec_eps

                    # we know everything we have to
                    if xref[0] and act_eps:
                        act_pos = (self.shared_memory.rec_X[1],
                                   -self.shared_memory.rec_Y[1])
                        xref = (xref[0], -xref[1])
                        
                        print(xref, act_eps)
                        # generate reference
                        alpha, foot, ptime, pose_id =  \
                            ref_generator.get_next_reference(
                                act_pos, act_eps, xref)
                        print(pose_id)
                        dvtsk, pvtsk = convert_ref(
                                clb.get_pressure(alpha, version), foot)
                        # send to main thread
                        self.shared_memory.dvalve_task = dvtsk
                        self.shared_memory.ref_task = pvtsk
                        # organisation
                        self.process_time = ptime
                        self.last_process_time = time.time()

                time.sleep(UI_TSAMPLING)
                set_leds()
            return (self.ui_state)

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- RUN STATE MACHINE ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        automat = state_machine.StateMachine()
        automat.add_state('PAUSE', pause_state)
        automat.add_state('PWM_FEED_THROUGH', pwm_feed_through)
        automat.add_state('USER_REFERENCE', user_reference)
        automat.add_state('APRILTAG_REFERENCE', apriltag_reference)
        automat.add_state('EXIT', exit_cleaner)
        automat.add_state('QUIT', None, end_state=True)
        automat.set_start('PAUSE')

        try:
            self.lcd.message('Select Operating Mode')
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
        self.lcd.message = 'Bye Bye ...'
        self.ui_state = 'EXIT'


n_dvalves = len(SWITCHES)
n_pvalves = len(POTIS)


def convert_ref(pressure, foot):
    dv_task, pv_task = {}, {}
    for jdx, dp in enumerate(foot):
        dv_task[jdx] = dp
    for kdx, pp in enumerate(pressure):
        pv_task[kdx] = pp

    return dv_task, pv_task


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
    def __init__(self, shared_memory, plotsock=None, IMU=False, IMG=False):
        threading.Thread.__init__(self)
        self.shared_memory = shared_memory
        self.state = 'RUN'
        self.plotsock = plotsock
        self.IMU_connected = True if IMU else False
        self.IMG_connected = True if IMG else False

    def prepare_data(self):
        p = [round(self.shared_memory.rec[i], 2) for i in range(8)]
        r = [round(self.shared_memory.ref_task[i], 2) for i in range(8)]
        u = [round(self.shared_memory.rec_u[i], 2) for i in range(8)]
        f = [round(self.shared_memory.dvalve_task[i], 2) for i in range(4)]

        if self.IMG_connected:
            aIMG = [round(self.shared_memory.rec_aIMG[i], 2)
                    if self.shared_memory.rec_aIMG[i] else None
                    for i in range(8)]
            eps = (round(self.shared_memory.rec_eps, 2)
                   if self.shared_memory.rec_eps else None)
            X = [round(self.shared_memory.rec_X[i], 2)
                 if self.shared_memory.rec_X[i] else None for i in range(8)]
            Y = [round(self.shared_memory.rec_Y[i], 2)
                 if self.shared_memory.rec_Y[i] else None for i in range(8)]
        else:
            aIMG, eps, X, Y = [None]*8, None, [None]*8, [None]*8

        if self.IMU_connected:
            rec_angle = self.shared_memory.rec_aIMU
            aIMU = [round(rec_angle[i], 2) if rec_angle[i]
                    else None for i in range(8)]
        else:
            aIMU = [None]*8

        return (p, r, u, f, aIMG, eps, X, Y, aIMU,
                self.IMU_connected, self.IMG_connected)

    def print_state(self):
        p, r, u, f, aIMG, eps, X, Y, aIMU, _, _ = self.prepare_data()
        eps = [eps] + [None]*3
        state_str = '\n\t| Ref \t| State \t| epsilon \n'
        state_str = state_str + '-------------------------------------------\n'
        for i in range(4):
            s = '{}\t| {}\t| {} \t\t| {}\n'.format(
                i, 1.0 if GPIO.input(SWITCHES[i]) else 0.0,
                self.shared_memory.dvalve_task[i], eps[i])
            state_str = state_str + s
        state_str = (
            state_str
            + '\n\t| Ref \t| p \t| PWM \t| aIMU \t| aIMG \t| POS  \n')
        state_str = state_str + '-'*75 + '\n'
        for i in range(8):
            s = '{}\t| {}\t| {}\t| {}\t| {}\t| {}\t| ({},{})\n'.format(
                i, r[i], p[i], u[i], aIMU[i], aIMG[i], X[i], Y[i])
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
