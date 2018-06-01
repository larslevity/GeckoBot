#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May 31 10:17:29 2018

@author: bianca
"""


import time
import logging

logPath = "/home/debian/Git/GeckoBot/boot_autorun_test/log/"
fileName = 'testlog'

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)


fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
    

try:
    import Adafruit_BBIO.GPIO as GPIO
    rootLogger.info('Succesfully imported BBIO.GPIO modules')
except ImportError as err:
    rootLogger.error(err, exc_info=True)

try:
    import Adafruit_BBIO.PWM as PWM
    rootLogger.info('Succesfully imported BBIO.PWM modules')
except ImportError as err:
    rootLogger.error(err, exc_info=True)




PWMLED = "P8_15"  # "P8_16"
PRESSURELED = "P8_14"  # "P8_15"
PATTERNLED = "P8_17"
WALKINGCONFIRMLED = "P8_16"  # "P8_18"
INFINITYLED = "P8_18"


GPIO.setup(PWMLED, GPIO.OUT)
GPIO.setup(PRESSURELED, GPIO.OUT)
GPIO.setup(PATTERNLED, GPIO.OUT)
GPIO.setup(WALKINGCONFIRMLED, GPIO.OUT)
GPIO.setup(INFINITYLED, GPIO.OUT)

if PWM:
    try:
        rootLogger.info('Try to start PWM duty cycle')
        PWM.start('P9_42', 0, 25000)
        PWM.start('P9_28', 0, 25000)
        rootLogger.info('Started PWM duty cycle')
    except Exception as err:
        rootLogger.error(err, exc_info=True)


leds = [PWMLED, PRESSURELED, PATTERNLED, WALKINGCONFIRMLED, INFINITYLED]
t_start = time.time()

while time.time()-t_start < 120:
    for led in leds:
        GPIO.output(led, GPIO.HIGH)
        time.sleep(.05)
        GPIO.output(led, GPIO.LOW)
    time.sleep(.05)
