#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 24 16:40:45 2019

@author: bianca
"""

from Src.Management import timeout
from Src.Management import exception
from Src.Visual.PiCamera import client


pc_ip = '134.28.136.131'

with timeout.timeout(2):
    try:
        plotsock = client.LivePlotterSocket(pc_ip)
        print("Connected to LivePlot Server")
    except exception.TimeoutError:
        print("Live Plot Server not found")


try:
    for i in range(100):
        print plotsock.send_sample({'p1': i, 'p2': i/2., 'u1': i**(.5)})

finally:
    plotsock.close()