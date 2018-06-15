# -*- coding: utf-8 -*-
"""
Created on Mon May 07 14:01:53 2018

@author: AmP
"""

from __future__ import print_function

import __builtin__
import threading
import time
import sys
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

from termcolor import colored

TSamplingUI = .1
p7_ptrn = 0.0

PWMREFMODE = "P9_23"
PRESSUREREFMODE = "P9_27"
PATTERNREFMODE = 'P9_30'  # "P9_25"  # 25 doesnt work.

WALKINGCONFIRM = "P9_24"
INFINITYMODE = "P9_26"

PWMLED = "P8_15"  # "P8_16"
PRESSURELED = "P8_14"  # "P8_15"
PATTERNLED = "P8_17"
WALKINGCONFIRMLED = "P8_16"  # "P8_18"
INFINITYLED = "P8_18"

DISCRETEPRESSUREREF = ["P9_11", "P9_17", "P9_15", "P9_13"]
CONTINUOUSPRESSUREREF = ["P9_40", "P9_38", "P9_33", "P9_39", "P9_36",
                         "P9_35", "P9_37"]


def print(*args, **kwargs):
    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


def generate_pattern(p0, p1, p2, p3, p4, p5, p6, p7):
    t_move = 2.0
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
    def __init__(self, cargo, rootLogger=None):
        """ """
        threading.Thread.__init__(self)
        self.cargo = cargo
        self.lastconfirm = time.time()
        self.lastinfmode = time.time()
        self.refzero = False
        self.rootLogger = rootLogger

        self.rootLogger.info('Initialize HUI Thread ...')
        ADC.setup()

        GPIO.setup(PWMREFMODE, GPIO.IN)
        GPIO.setup(PRESSUREREFMODE, GPIO.IN)
        GPIO.setup(PATTERNREFMODE, GPIO.IN)
        GPIO.setup(WALKINGCONFIRM, GPIO.IN)
        GPIO.setup(INFINITYMODE, GPIO.IN)

        GPIO.setup(PWMLED, GPIO.OUT)
        GPIO.setup(PRESSURELED, GPIO.OUT)
        GPIO.setup(PATTERNLED, GPIO.OUT)
        GPIO.setup(WALKINGCONFIRMLED, GPIO.OUT)
        GPIO.setup(INFINITYLED, GPIO.OUT)

        for pin in DISCRETEPRESSUREREF:
            GPIO.setup(pin, GPIO.IN)
#        for pin in CONTINUOUSPRESSUREREF:
#            GPIO.setup(pin, GPIO.IN)

        GPIO.add_event_detect(PWMREFMODE, GPIO.RISING)
        GPIO.add_event_detect(PRESSUREREFMODE, GPIO.RISING)
        GPIO.add_event_detect(PATTERNREFMODE, GPIO.RISING)
        GPIO.add_event_detect(WALKINGCONFIRM, GPIO.RISING)
        GPIO.add_event_detect(INFINITYMODE, GPIO.RISING)

        self.leds = [PWMLED, PRESSURELED, PATTERNLED,
                     WALKINGCONFIRMLED, INFINITYLED]

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
        if GPIO.event_detected(INFINITYMODE):
            print('Infmode btn pushed')
        if GPIO.event_detected(WALKINGCONFIRM):
            print('WALKING START btn pushed')

        # check adc potis
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            val = ADC.read(pin)
            val = ADC.read(pin)
            print('POTI Ref', idx, ': ', val)
        time.sleep(1)

        print('\n')

    def get_tasks(self):
        state, _ = self.check_state()
        self.set_leds()
        if state == 'USER_CONTROL':
            self.process_pwm_ref()
        elif state == 'USER_REFERENCE':
            self.process_pressure_ref()
        elif state == 'REFERENCE_TRACKING':
            self.process_pattern_ref()
        elif state == 'IMU_CONTROL':
            self.process_imu_control()
#        self.print_state()

    def process_imu_control(self):
        self.change_state('IMU_CONTROL')
        self.set_dvalve()
        self.set_ref()
#        self.set_ctr_gain()

    def process_pressure_ref(self):
        self.change_state('USER_REFERENCE')
        self.set_refzero()
        self.set_ref()
        self.set_dvalve()

    def check_p28(self):
        if GPIO.event_detected(INFINITYMODE):
            self.cargo.pwm_task['7'] = 80.
            time.sleep(1)
            self.cargo.pwm_task['7'] = 0.

    def process_pwm_ref(self):
        self.change_state('USER_CONTROL')
        self.set_valve()
        self.set_dvalve()
#        # DEBUG
#        self.check_p28()

    def process_pattern_ref(self):
        self.change_state('REFERENCE_TRACKING')
        self.set_pattern()
        self.set_walking()
        # self.set_infmode()
        self.set_userpattern()

    def check_state(self):
        new_state = None
        if GPIO.event_detected(PWMREFMODE):
            new_state = 'USER_CONTROL'
        elif GPIO.event_detected(PRESSUREREFMODE):
            new_state = 'USER_REFERENCE'
        elif GPIO.event_detected(PATTERNREFMODE):
            new_state = 'REFERENCE_TRACKING'

        change = False
        if new_state:
            potis = []
            for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
                val = ADC.read(pin)
                val = ADC.read(pin)
                potis.append(round(val*100))
            if sum(potis) == 0:
                change = True
            else:
                for i in range(3):
                    for led in self.leds:
                        GPIO.output(led, GPIO.HIGH)
                    time.sleep(.05)
                    for led in self.leds:
                        GPIO.output(led, GPIO.LOW)
                    time.sleep(.05)
        return (new_state if change else self.cargo.state, change)

    def set_leds(self):
        actual_state = self.cargo.actual_state
        for pin, state in [(PWMLED, "USER_CONTROL"),
                           (PRESSURELED, "USER_REFERENCE"),
                           (PATTERNLED, "REFERENCE_TRACKING")]:
            GPIO.output(pin, GPIO.HIGH if actual_state == state else GPIO.LOW)
        if actual_state == 'REFERENCE_TRACKING':
            for pin, state in [(WALKINGCONFIRMLED, self.cargo.wcomm.is_active),
                               # (INFINITYLED, self.cargo.wcomm.infmode)
                               (INFINITYLED, self.cargo.wcomm.user_pattern)
                               ]:
                GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
        elif actual_state == "USER_REFERENCE":
            GPIO.output(INFINITYLED, GPIO.HIGH if self.refzero else GPIO.LOW)

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
            if self.refzero:
                self.cargo.ref_task[str(idx)] = 0.
            else:
                _ = ADC.read(pin)
                self.cargo.ref_task[str(idx)] = round(ADC.read(pin)*100)/100.

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

    def set_dvalve(self):
        for idx, pin in enumerate(DISCRETEPRESSUREREF):
            self.cargo.dvalve_task[str(idx)] = (
                True if GPIO.input(pin) else False)

    def set_walking(self):
        if GPIO.event_detected(WALKINGCONFIRM):
            if time.time()-self.lastconfirm > 1:
                confirm = self.cargo.wcomm.confirm
                self.cargo.wcomm.confirm = not confirm
                self.rootLogger.info(
                        'Walking was turned {}'.format(not confirm))
                self.lastconfirm = time.time()

    def set_infmode(self):
        if GPIO.event_detected(INFINITYMODE):
            if time.time()-self.lastinfmode > 1:
                state = self.cargo.wcomm.infmode
                self.cargo.wcomm.infmode = not state
                self.rootLogger.info('Infmode was turned {}'.format(not state))
                self.lastinfmode = time.time()

    def set_ctr_gain(self):
        if GPIO.event_detected(INFINITYMODE):
            if time.time()-self.lastinfmode > 1:
                P, I, D = self.tune_imu_ctr()
                self.rootLogger.info('ctr_gain was set to {}'.format([P, I, D]))
                self.lastinfmode = time.time()

    def tune_imu_ctr(self):
        PIDimu = [1.05/90., 0.03*20., 0.01]

        gain = []
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF[1:4]):
            _ = ADC.read(pin)
            gain.append(round(ADC.read(pin)*100)/100.)

        P, I, D = (PIDimu[0]+gain[0]*.3, PIDimu[0]+gain[2]*1,
                   PIDimu[2]+gain[2]*.3)
        self.cargo.imu_ctr[0].set_gain([P, I, D])
        return P, I, D

    def set_refzero(self):
        if GPIO.event_detected(INFINITYMODE):
            if time.time()-self.lastinfmode > 1:
                state = self.refzero
                self.refzero = not state
                self.rootLogger.info('RefZero was turned {}'.format(not state))
                self.lastinfmode = time.time()

    def set_userpattern(self):
        if GPIO.event_detected(INFINITYMODE):
            if time.time()-self.lastinfmode > 1:
                state = self.cargo.wcomm.user_pattern
                self.cargo.wcomm.user_pattern = not state
                self.rootLogger.info(
                        'user_pattern was turned {}'.format(not state))
                self.lastinfmode = time.time()
                if state:  # user_pattern was True -> now its False
                    self.cargo.wcomm.pattern = \
                        self.cargo.wcomm.ptrndic['default']

    def kill(self):
        self.cargo.state = 'EXIT'

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
