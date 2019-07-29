# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 15:23:07 2019

@author: AmP
"""

from __future__ import print_function


import threading
import time
import sys
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import logging

from Src.Management import state_machine
from Src.Controller.UserControl import default as feature
from Src.Hardware import lcd as lcd_module

rootLogger = logging.getLogger()
lcd = lcd_module.getlcd()

UI_TSAMPLING = .1

MODE1 = "P9_23"
MODE2 = "P9_27"
MODE3 = "P9_30"  # "P9_25" doesnt work.
MODES = [MODE1, MODE2, MODE3]

FUN1 = "P9_24"
FUN2 = "P9_26"
BTNS = [MODE1, MODE2, MODE3, FUN1, FUN2]

MODE1LED = "P8_15"
MODE2LED = "P8_14"
MODE3LED = "P8_17"
FUN1LED = "P8_16"
FUN2LED = "P8_18"
LEDS = [MODE1LED, MODE2LED, MODE3LED, FUN1LED, FUN2LED]

SWITCHES = {0: "P9_11", 1: "P9_17", 2: "P9_15", 3: "P9_13"}
POTIS = {0: "P9_40", 1: "P9_38", 2: "P9_33", 3: "P9_39",
         4: "P9_36", 5: "P9_35", 6: "P9_37"}


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


def get_initial_pose(pattern, hold0=5., hold1=1.):
    ref0 = pattern[0]
    ref0 = ref0[:8] + [False]*4 + [hold0]
    ref1 = ref0[:8] + [False, True, True, False] + [hold1]
    return [ref0, ref1]


class UserInterface(threading.Thread):
    def __init__(self):
        """ """
        threading.Thread.__init__(self)

        self.state = 'MODE1'

        self.lastfun1 = time.time()
        self.lastfun2 = time.time()
        self.lastchange = time.time()
        self.fun1 = False
        self.fun2 = False

        rootLogger.info('Initialize UserInterface ...')

        ADC.setup()

        for btn in BTNS:
            GPIO.setup(btn, GPIO.IN)
            GPIO.add_event_detect(btn, GPIO.RISING)
        for led in LEDS:
            GPIO.setup(led, GPIO.OUT)
        for idx in SWITCHES:
            GPIO.setup(SWITCHES[idx], GPIO.IN)
        ring_leds()

    def run(self):
        """ run HUI """
        rootLogger.info('Running HUI Thread ...')

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- HELP FUNCTIONS    ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        def mode_changed():
            new_state = None
            if GPIO.event_detected(MODE1):
                new_state = 'MODE1'
            elif GPIO.event_detected(MODE2):
                new_state = 'MODE2'
            elif GPIO.event_detected(MODE3):
                new_state = 'MODE3'
            elif self.state == 'EXIT':
                new_state = 'EXIT'

            change = False
            if new_state and time.time()-self.lastchange > 1:
                if (all_potis_zero() and new_state is not self.state
                        or new_state == 'EXIT'):
                    change = True
                    self.state = new_state
                    rootLogger.info("UI goes to: {}".format(new_state))
                    reset_events()
                    self.lastchange = time.time()
                else:
                    flicker_leds()
            return change

        def fun1():
            if GPIO.event_detected(FUN1):
                if time.time()-self.lastfun1 > 1:
                    state = self.fun1
                    self.fun1 = not state
                    rootLogger.info('Fun1 turned {}'.format(not state))
                    self.lastfun1 = time.time()
            return self.fun1

        def fun2():
            if GPIO.event_detected(FUN2):
                if time.time()-self.lastfun2 > 1:
                    state = self.fun2
                    self.fun2 = not state
                    rootLogger.info('Fun2 turned {}'.format(not state))
                    self.lastfun2 = time.time()
            return self.fun2

        def reset_events():
            for btn in BTNS:
                GPIO.event_detected(btn)
            self.fun1 = False
            self.fun2 = False

        def set_leds():
            my_state = self.state
            for pin, state in [(MODE1LED, 'MODE1'), (MODE2LED, 'MODE2'),
                               (MODE3LED, 'MODE3')]:
                GPIO.output(pin, GPIO.HIGH if my_state == state else GPIO.LOW)
            for pin, state in [(FUN1LED, self.fun1), (FUN2LED, self.fun2)]:
                GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- STATE HANDLERS    ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        def exit_cleaner():
            # Clean?
            return ('QUIT')

        def mode1():
            lcd.display(feature.NAMES[0])
            while not mode_changed():

                fun = [fun1(), fun2()]
                switches = read_switches()
                potis = read_potis()

                feature.mode1(switches, potis, fun)

                time.sleep(UI_TSAMPLING)
                set_leds()
            return self.state

        def mode2():
            lcd.display(feature.NAMES[1])
            while not mode_changed():

                fun = [fun1(), fun2()]
                switches = read_switches()
                potis = read_potis()

                feature.mode2(switches, potis, fun)

                time.sleep(UI_TSAMPLING)
                set_leds()
            return self.state

        def mode3():
            lcd.display(feature.NAMES[2])
            while not mode_changed():

                fun = [fun1(), fun2()]
                switches = read_switches()
                potis = read_potis()

                feature.mode3(switches, potis, fun)

                time.sleep(UI_TSAMPLING)
                set_leds()
            return self.state

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- RUN STATE MACHINE ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

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
            rootLogger.exception('\n exception HUI Thread \n')
            rootLogger.exception(
                    "Unexpected error:\n", sys.exc_info()[0])
            rootLogger.exception(sys.exc_info()[1])
            rootLogger.error(err, exc_info=True)

        rootLogger.info('HUI Thread is done ...')

    def kill(self):
        self.state = 'EXIT'
