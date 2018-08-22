# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 15:45:16 2018

@author: Lars Schiller
"""

from __future__ import print_function

import __builtin__
import threading
import time
import sys
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

from termcolor import colored
from Src.Management import reference as ref
from Src.Management import state_machine

TSamplingUI = .1
p7_ptrn = 0.0

MODE1 = "P9_23"
MODE2 = "P9_27"
MODE3 = 'P9_30'  # "P9_25" doesnt work.

FUN1 = "P9_24"
FUN2 = "P9_26"

BTNS = [MODE1, MODE2, MODE3, FUN1, FUN2]

MODE1LED = "P8_15"  # "P8_16"
MODE2LED = "P8_14"
MODE3LED = "P8_17"
FUN1LED = "P8_16"
FUN2LED = "P8_18"

DISCRETEPRESSUREREF = ["P9_11", "P9_17", "P9_15", "P9_13"]
CONTINUOUSPRESSUREREF = ["P9_40", "P9_38", "P9_33", "P9_39", "P9_36",
                         "P9_35", "P9_37"]


def print(*args, **kwargs):
    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


def generate_pattern(p0, p1, p2, p3, p4, p5, p6, p7):
    t_move = 3.0
    t_fix = .66
    t_dfx = .25
    p01 = 0.25
    p11 = 0.25
    p41 = 0.25
    p51 = 0.25
    data = [
        [p01, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, False, t_move],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, False, False, True, t_dfx],
        [p0, p11, 0.0, p3, p4, p51, 0.0, p7, True, False, False, True, t_move],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, False, True, True, False, t_dfx]
    ]
    return data


class HUIThread(threading.Thread):
    def __init__(self, shared_memory, rootLogger=None):
        """ """
        threading.Thread.__init__(self)
        self.shared_memory = shared_memory
        self.lastfun1 = time.time()
        self.lastfun1 = time.time()
        self.lastfun2 = time.time()
        self.fun1 = False
        self.fun2 = False

        self.rootLogger = rootLogger
        self.ptrn_idx = 0
        self.last_process_time = time.time()
        self.process_time = 0
        self.state = cargo.state

        self.rootLogger.info('Initialize HUI Thread ...')
        ADC.setup()

        GPIO.setup(MODE1, GPIO.IN)
        GPIO.setup(MODE2, GPIO.IN)
        GPIO.setup(MODE3, GPIO.IN)
        GPIO.setup(FUN1, GPIO.IN)
        GPIO.setup(FUN2, GPIO.IN)

        GPIO.setup(MODE1LED, GPIO.OUT)
        GPIO.setup(MODE2LED, GPIO.OUT)
        GPIO.setup(MODE3LED, GPIO.OUT)
        GPIO.setup(FUN1LED, GPIO.OUT)
        GPIO.setup(FUN2LED, GPIO.OUT)

        for pin in DISCRETEPRESSUREREF:
            GPIO.setup(pin, GPIO.IN)

        GPIO.add_event_detect(MODE1, GPIO.RISING)
        GPIO.add_event_detect(MODE2, GPIO.RISING)
        GPIO.add_event_detect(MODE3, GPIO.RISING)
        GPIO.add_event_detect(FUN1, GPIO.RISING)
        GPIO.add_event_detect(FUN2, GPIO.RISING)

        self.leds = [MODE1LED, MODE2LED, MODE3LED,
                     FUN1LED, FUN2LED]

        for i in range(5):
            for led in self.leds:
                GPIO.output(led, GPIO.HIGH)
                time.sleep(.05)
                GPIO.output(led, GPIO.LOW)
            time.sleep(.05)

    def run(self):
        """ run HUI """
        self.rootLogger.info('Running HUI Thread ...')
        excp_str = (
            '\n----------caught exception! in HUI Thread----------------\n')
        try:
            while self.cargo.state != 'EXIT':
                try:
                    self.get_tasks()
                    time.sleep(TSamplingUI)
                except Exception as err:
                    self.rootLogger.exception(excp_str)
                    self.rootLogger.exception(
                            "Unexpected error:\n", sys.exc_info()[0])
                    self.rootLogger.exception(sys.exc_info()[1])
                    self.rootLogger.error(err, exc_info=True)
                    self.rootLogger.info('\nBreaking the HUI loop ...')
                    break
        finally:
            self.rootLogger.info('Exit the HUI Thread ...')
            self.cargo.state = 'EXIT'

        self.rootLogger.info('HUI Thread is done ...')

    def test_the_thing(self):
        state, change = self.check_state()
        if change:
            print(state)

        for idx, pin in enumerate(DISCRETEPRESSUREREF):
            print('DValve Ref', idx, ': ', True if GPIO.input(pin) else False)

        # check pattern btns
        if GPIO.event_detected(FUN2):
            print('Mode2 btn pushed')
        if GPIO.event_detected(FUN1):
            print('WALKING START btn pushed')

        # check adc potis
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            val = ADC.read(pin)
            val = ADC.read(pin)
            print('POTI Ref', idx, ': ', val)
        time.sleep(1)

        print('\n')

    def get_tasks(self):
        state, change = self.check_state()
        if change:
            self.reset_events()
            self.reset_confirmations()
        self.set_leds()
        if state == 'USER_REFERENCE':
            self.process_user_ref()
        elif state == 'PATTERN_REF':
            self.process_pattern_ref()
        elif state == 'USER_CONTROL':
            self.process_pwm_ref()
#        self.print_state()

    def process_user_ref(self):
        self.set_mode2() 
        if not self.fun2:
            self.change_state('USER_REFERENCE')
        else:
            self.change_state('IMU_CONTROL')
        self.set_refzero()
        self.set_ref()
        self.set_dvalve()

    def process_pwm_ref(self):
        self.change_state('USER_CONTROL')
        self.set_valve()
        self.set_dvalve()

    def process_pattern_ref(self):
        self.set_mode2() 
        if not self.fun2:
            self.change_state('USER_REFERENCE')
        else:
            self.change_state('IMU_CONTROL')
        self.set_pattern()
        self.set_walking()
        self.set_userpattern()
        if self.cargo.wcomm.confirm:
            self.cargo.wcomm.is_active = True
            if self.last_process_time + self.process_time < time.time():
                self.process_time = self.generate_pattern_ref()
                self.last_process_time = time.time()

    def generate_pattern_ref(self):
        pattern = self.cargo.wcomm.pattern
        idx = self.ptrn_idx
        idx = idx+1 if idx<len(pattern)-1 else 0
        dvtask, pvtask, process_time = ref.generate_walking_ref(pattern, idx)
        self.cargo.dvalve_task = dvtask
        self.cargo.ref_task = pvtask
        self.ptrn_idx = idx
        return process_time


    def check_state(self):
        new_state = None
        if GPIO.event_detected(MODE1):
            new_state = 'USER_CONTROL'
        elif GPIO.event_detected(MODE2):
            new_state = 'USER_REFERENCE'
        elif GPIO.event_detected(MODE3):
            new_state = 'PATTERN_REF'

        change = False
        if new_state:
            if self.all_potis_zero():
                change = True
            else:
                for i in range(3):
                    for led in self.leds:
                        GPIO.output(led, GPIO.HIGH)
                    time.sleep(.05)
                    for led in self.leds:
                        GPIO.output(led, GPIO.LOW)
                    time.sleep(.05)
        self.state = new_state if change else self.state
        return (self.state, change)

    def set_leds(self):
        my_state = self.state
        for pin, state in [(MODE1LED, "USER_CONTROL"),
                           (MODE2LED, "USER_REFERENCE"),
                           (MODE3LED, "PATTERN_REF")]:
            GPIO.output(pin, GPIO.HIGH if my_state == state else GPIO.LOW)
        if my_state == 'PATTERN_REF':
            for pin, state in [(FUN1LED, self.cargo.wcomm.is_active),
                               (FUN2LED, self.fun2)
                               ]:
                GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
        elif my_state == "USER_REFERENCE":
            GPIO.output(FUN2LED, GPIO.HIGH if self.fun2 else GPIO.LOW)
            GPIO.output(FUN1LED, GPIO.HIGH if self.fun1 else GPIO.LOW)
        elif my_state == "USER_CONTROL":
            GPIO.output(FUN2LED, GPIO.LOW)
            GPIO.output(FUN1LED, GPIO.LOW)
        elif my_state == "IMU_CONTROL":
            GPIO.output(FUN2LED, GPIO.LOW)
            GPIO.output(FUN1LED, GPIO.LOW)

    def change_state(self, state):
        self.cargo.state = state
        while not self.cargo.actual_state == state:
            time.sleep(self.cargo.sampling_time)

    def set_valve(self):
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            _ = ADC.read(pin)  # bug-> read twice
            self.cargo.pwm_task[str(idx)] = round(ADC.read(pin)*100)

    def set_ref(self):
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            if self.fun1:
                self.cargo.ref_task[str(idx)] = 0.
            else:
                _ = ADC.read(pin)
                self.cargo.ref_task[str(idx)] = round(ADC.read(pin)*100)/100.

    def set_dvalve(self):
        for idx, pin in enumerate(DISCRETEPRESSUREREF):
            self.cargo.dvalve_task[str(idx)] = (
                True if GPIO.input(pin) else False)

    def set_walking(self):
        if GPIO.event_detected(FUN1):
            if time.time()-self.lastfun1 > 1:
                confirm = self.cargo.wcomm.confirm
                self.cargo.wcomm.confirm = not confirm
                self.rootLogger.info(
                        'Walking was turned {}'.format(not confirm))
                self.lastfun1 = time.time()

    def set_mode2(self):
        if GPIO.event_detected(FUN2):
            if time.time()-self.lastfun2 > 1:
                state = self.fun2
                self.fun2 = not state
                self.rootLogger.info('Mode2 was turned {}'.format(not state))
                self.lastfun2 = time.time()

    def set_refzero(self):
        if GPIO.event_detected(FUN1):
            if time.time()-self.lastfun1 > 1:
                state = self.fun1
                self.fun1 = not state
                self.rootLogger.info('RefZero was turned {}'.format(not state))
                self.lastfun1 = time.time()

    def set_userpattern(self):
        if self.all_potis_zero():
            if self.cargo.wcomm.user_pattern:
                self.cargo.wcomm.user_pattern = False
                self.cargo.wcomm.pattern = self.cargo.wcomm.ptrndic['default']
                self.rootLogger.info('user_pattern was turned False')
        else:
            if not self.cargo.wcomm.user_pattern:
                self.cargo.wcomm.user_pattern = True
                self.rootLogger.info('user_pattern was turned True')

    def set_pattern(self):
        if self.cargo.wcomm.user_pattern:
            pref = []
            for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
                _ = ADC.read(pin)
                pref.append(round(ADC.read(pin)*100)/100.)
            pref.append(p7_ptrn)
            pattern = generate_pattern(*pref)
            self.cargo.wcomm.pattern = pattern
#        else:
#            self.cargo.wcomm.pattern = self.cargo.wcomm.ptrndic['default']

    def all_potis_zero(self):
        zero = False
        potis = []
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            val = ADC.read(pin)
            val = ADC.read(pin)
            potis.append(round(val*100))
        if sum(potis) == 0:
            zero = True
        return zero

    def kill(self):
        self.cargo.state = 'EXIT'

    def reset_events(self):
        for btn in BTNS:
            GPIO.event_detected(btn)

    def reset_confirmations(self):
        self.fun1 = False
        self.fun2 = False
        self.fun1 = False
        self.cargo.wcomm.confirm = False
        self.cargo.wcomm.is_active = False

    def print_state(self):
        state_str = ('Current State: \n\n' +
                     'F1 Ref/state: \t\t{}\t{}\n'.format(
                             True if GPIO.input(DISCRETEPRESSUREREF[0])
                             else False, self.cargo.dvalve_task['0']) +
                     'F2 Ref/state: \t\t{}\t{}\n'.format(
                             True if GPIO.input(DISCRETEPRESSUREREF[1])
                             else False, self.cargo.dvalve_task['1']) +
                     'F3 Ref/state: \t\t{}\t{}\n'.format(
                             True if GPIO.input(DISCRETEPRESSUREREF[2])
                             else False, self.cargo.dvalve_task['2']) +
                     'F4 Ref/state: \t\t{}\t{}\n'.format(
                             True if GPIO.input(DISCRETEPRESSUREREF[3])
                             else False, self.cargo.dvalve_task['3'])
                     )
        for i in range(8):
            s = 'PWM Ref {}: \t\t{}\n'.format(i, self.cargo.pwm_task[str(i)])
            state_str = state_str + s
        for i in range(8):
            s = 'Pressure {} Ref/state \t{}\t{}\n'.format(
                    i, self.cargo.ref_task[str(i)], self.cargo.rec[str(i)])
            state_str = state_str + s
        print(state_str)


#    def set_ctr_gain(self):
#        if GPIO.event_detected(FUN2):
#            if time.time()-self.lastinfmode > 1:
#                P, I, D = self.tune_imu_ctr()
#                self.rootLogger.info('ctr_gain was set to {}'.format([P, I, D]))
#                self.lastinfmode = time.time()
#
#    def tune_imu_ctr(self):
#        PIDimu = [1.05/90., 0.03*20., 0.01]
#
#        gain = []
#        for idx, pin in enumerate(CONTINUOUSPRESSUREREF[1:4]):
#            _ = ADC.read(pin)
#            gain.append(round(ADC.read(pin)*100)/100.)
#
#        P, I, D = (PIDimu[0]+gain[0]*.3, PIDimu[0]+gain[2]*1,
#                   PIDimu[2]+gain[2]*.3)
#        self.cargo.imu_ctr[0].set_gain([P, I, D])
#        return P, I, D
