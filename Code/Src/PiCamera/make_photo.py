#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 15:33:24 2019

@author: bianca
"""


import picamera
import time


with picamera.PiCamera() as camera:
    # camera.resolution = (2592, 1944)
    camera.resolution = (1648, 1232)
    # Start a preview and let the camera warm up for 2 seconds
    camera.start_preview()
    time.sleep(2)
    
    camera.capture(time.strftime('photo_%Y-%m-%d--%H-%M-%S.jpg'))
