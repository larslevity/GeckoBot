#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May 31 10:17:29 2018

@author: bianca
"""

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
    import Adafruit_BBIO.PWM as PWM
    rootLogger.info('Succesfully imported BBIO.PWM modules')
except ImportError as err:
    rootLogger.error(err, exc_info=True)


if PWM:
    try:
        rootLogger.info('Try to start PWM duty cycle')
        PWM.start('P9_42', 0, 25000)
        PWM.start('P9_28', 0, 25000)
        PWM.stop('P9_42')
        PWM.stop('P9_28')
        rootLogger.info('Started PWM duty cycle')
    except Exception as err:
        rootLogger.error(err, exc_info=True)