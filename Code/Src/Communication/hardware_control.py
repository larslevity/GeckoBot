# -*- coding: utf-8 -*-
"""
Created on Mon May 07 14:01:53 2018

@author: AmP
"""

from __future__ import print_function

import __builtin__
import threading
import time
import traceback
import sys
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

from termcolor import colored

TSamplingUI = 1

PWMREFMODE = "P9_23"
PRESSUREREFMODE = "P9_27"
PATTERNREFMODE = 'P9_30'  # "P9_25"  # 25 doesnt work.

WALKINGCONFIRM = "P9_24"
INFINITYMODE = "P9_26"

PWMLED = "P8_15"  #"P8_16"
PRESSURELED = "P8_14"  # "P8_15"
PATTERNLED = "P8_17"
WALKINGCONFIRMLED = "P8_16"  # "P8_18"
INFINITYLED = "P8_18"

# DISCRETEPRESSUREREF = ["P9_11", "P9_13", "P9_15", "P9_17"]
DISCRETEPRESSUREREF = ["P9_11", "P9_17", "P9_15", "P9_13"]

#
#CONTINUOUSPRESSUREREF = ["P9_40", "P9_33", "P9_39", "P9_36",
#                         "P9_35", "P9_37", "P9_38"]

CONTINUOUSPRESSUREREF = ["P9_40", "P9_38", "P9_33", "P9_39", "P9_36",
                         "P9_35", "P9_37"]



def print(*args, **kwargs):
    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


class HUIThread(threading.Thread):
    def __init__(self, cargo):
        """ """
        threading.Thread.__init__(self)
        self.cargo = cargo

        print('Initialize HUI Thread ...')
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
        print('Running HUI Thread ...')

        try:
            while self.cargo.state != 'EXIT':
                try:
                    self.get_tasks()
                    time.sleep(TSamplingUI)
                except:
                    print('\n--caught exception! in HUI Thread--\n')
                    print("Unexpected error:\n", sys.exc_info()[0])
                    print(sys.exc_info()[1])
                    traceback.print_tb(sys.exc_info()[2])
                    print('\nBreaking the HUI loop ...')
                    break
        finally:
            print('Exit the HUI Thread ...')
            self.cargo.state = 'EXIT'

        print('HUI Thread is done ...')

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
        self.print_state()

    def process_pressure_ref(self):
        self.change_state('USER_REFERENCE')
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
        self.set_walking()
        self.set_infmode()

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
        for pin, state in [(WALKINGCONFIRMLED, self.cargo.wcomm.is_active),
                           (INFINITYLED, self.cargo.wcomm.infmode)]:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

    def change_state(self, state):
        self.cargo.state = state
        while not self.cargo.actual_state == state:
            time.sleep(self.cargo.sampling_time)

    def set_valve(self):
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            self.cargo.pwm_task[str(idx)] = ADC.read(pin)
            self.cargo.pwm_task[str(idx)] = round(ADC.read(pin)*100)  # bug-> read twice

    def set_ref(self):
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            self.cargo.ref_task[str(idx)] = ADC.read(pin)
            self.cargo.ref_task[str(idx)] = round(ADC.read(pin)*100)/100.

    def set_dvalve(self):
        for idx, pin in enumerate(DISCRETEPRESSUREREF):
            self.cargo.dvalve_task[str(idx)] = (
                True if GPIO.input(pin) else False)

    def set_walking(self):
        if GPIO.event_detected(WALKINGCONFIRM):
            confirm = self.cargo.wcomm.confirm
            self.cargo.wcomm.confirm = not confirm

    def set_infmode(self):
        if GPIO.event_detected(INFINITYMODE):
            state = self.cargo.wcomm.infmode
            self.cargo.wcomm.infmode = not state

    def kill(self):
        self.cargo.state = 'EXIT'

    def print_state(self):
        state_str = ('Current State: \n\n' +
            'F1 Ref/state: \t\t{}\t{}\n'.format(True 
                               if GPIO.input(DISCRETEPRESSUREREF[0]) 
                               else False, self.cargo.dvalve_task['0']) +
            'F2 Ref/state: \t\t{}\t{}\n'.format(True 
                               if GPIO.input(DISCRETEPRESSUREREF[1]) 
                               else False, self.cargo.dvalve_task['1']) +
            'F3 Ref/state: \t\t{}\t{}\n'.format(True 
                               if GPIO.input(DISCRETEPRESSUREREF[2]) 
                               else False, self.cargo.dvalve_task['2']) +
            'F4 Ref/state: \t\t{}\t{}\n'.format(True 
                               if GPIO.input(DISCRETEPRESSUREREF[3]) 
                               else False, self.cargo.dvalve_task['3'])
            )
        for i in range(8):
            s = 'PWM Ref {}: \t\t{}\n'.format(i, self.cargo.pwm_task[str(i)])
            state_str = state_str + s
        for i in range(8):
            s = 'Pressure {} Ref/state \t{}\t{}\n'.format(i,
                          self.cargo.ref_task[str(i)], self.cargo.rec[str(i)])
            state_str = state_str + s
        print(state_str)