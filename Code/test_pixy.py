#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 14 15:56:37 2020

@author: ls


VECTOR INDEX: This variable contains the tracking index of the Vector or line.
 When Pixy2 detects a new line, it will add it to a table of lines that it is
 currently tracking. It will then attempt to find the line (and every line in
 the table) in the next frame by finding its best match. Each line index will
 be kept for that line until the line either leaves Pixy2's field-of-view, or
 Pixy2 can no longer find the line in subsequent frames (because of occlusion,
 lack of lighting, etc.)

"""

import sys
from os import path
path2git = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.insert(0, path2git) # insert Git folder into path

from pixy2.build.python_demos import pixy
from pc_liveplotter_main import GuiThread
from test_ctrgui import GuiThread as CtrGuiThread


import time
import numpy as np
import subprocess

from ctypes import Structure, c_uint

class Vector (Structure):
  _fields_ = [
    ("m_x0", c_uint),
    ("m_y0", c_uint),
    ("m_x1", c_uint),
    ("m_y1", c_uint),
    ("m_index", c_uint),
    ("m_flags", c_uint) ]

class IntersectionLine (Structure):
  _fields_ = [
    ("m_index", c_uint),
    ("m_reserved", c_uint),
    ("m_angle", c_uint) ]

vectors = pixy.VectorArray(100)
intersections = pixy.IntersectionArray(100)
barcodes = pixy.BarcodeArray(100)
frame = 0



#def get_lines(get_all_features=True):
#    if get_all_features:
#        pixy.line_get_all_features()
#    else:
#        pixy.line_get_main_features()
#    i_count = pixy.line_get_intersections(100, intersections)
#    v_count = pixy.line_get_vectors(100, vectors)
#    b_count = pixy.line_get_barcodes(100, barcodes)
#    if i_count > 0 or v_count > 0 or b_count > 0:
#        for index in range (0, i_count):
#            print('[INTERSECTION: X=%d Y=%d BRANCHES=%d]' % (
#                    intersections[index].m_x,
#                    intersections[index].m_y,
#                    intersections[index].m_n))
#            for lineIndex in range (0, intersections[index].m_n):
#                print('  [LINE: INDEX=%d ANGLE=%d]' % (
#                        intersections[index].getLineIndex(lineIndex),
#                        intersections[index].getLineAngle(lineIndex)))
#        for index in range (0, v_count):
#            print('[VECTOR: INDEX=%d X0=%d Y0=%d X1=%d Y1=%d]' % (
#                    vectors[index].m_index,
#                    vectors[index].m_x0,
#                    vectors[index].m_y0,
#                    vectors[index].m_x1,
#                    vectors[index].m_y1))
#        for index in range (0, b_count):
#            print('[BARCODE: X=%d Y=%d CODE=%d]' % (
#                    barcodes[index].m_x,
#                    barcodes[index].m_y,
#                    barcodes[index].m_code))



def record(recorder):
    pixy.line_get_main_features()
    v_count = pixy.line_get_vectors(100, vectors)
    if v_count > 0:
        for index in range(0, v_count):
            sample = {'x{}'.format(index*2): vectors[index].m_x0,
                      'y{}'.format(index*2): -vectors[index].m_y0,
                      'x{}'.format(index*2+1): vectors[index].m_x1,
                      'y{}'.format(index*2+1): -vectors[index].m_y1,
                      'time': time.time()}

            recorder.append(sample)
            recorder.append({'vec': [vectors[index].m_x0,
                                     -vectors[index].m_y0, 
                                     vectors[index].m_x1,
                                     -vectors[index].m_y1],})
    else:
        sample = {'x0': np.nan,
                  'y0': np.nan,
                  'x1': np.nan,
                  'y1': np.nan,
                  'time': time.time()}
    
        recorder.append(sample)
        recorder.append({'vec': [np.nan, np.nan, np.nan, np.nan]})
          


gui = GuiThread(tsampling=.15)
gui.start()


pixy.init()
pixy.change_prog("line");
pixy.set_lamp(1,1)
time.sleep(.1)
pixy.set_servos(500, 500)

# init gui
for idx in range(10):
    record(gui.rec)
    time.sleep(.1)

gui.app.refresh_selection(mode='vec')




#get_frame()


try:
    frame = 0
    pixy.set_lamp(0,0)
    while gui.is_running():
        pan = gui.app.ctr.task.pan_val
        tilt = gui.app.ctr.task.tilt_val
        pixy.set_servos(pan, tilt)
        if frame%15 == 0:
            record(gui.rec)
#                    snap()
        time.sleep(.01)
        frame += 1
except KeyboardInterrupt:
    gui.kill()
#    ctrgui.kill()


finally:
    pixy.set_lamp(0,0)
