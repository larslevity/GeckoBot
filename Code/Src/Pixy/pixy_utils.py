# -*- coding: utf-8 -*-
"""
Created on Tue May 26 15:04:16 2020

@author: AmP
"""

import threading

from ctypes import Structure, c_uint
import time
import numpy as np

import sys
from os import path
path2git = path.dirname(path.dirname(path.dirname(path.abspath(
        (sys.modules['__main__'].__file__)))))
sys.path.insert(0, path2git)  # insert Git folder into path

from pixy2.build.python_demos import pixy
from Src.Controller import gait_law_planner as gaitlaw


class Vector (Structure):
    _fields_ = [
        ("m_x0", c_uint),
        ("m_y0", c_uint),
        ("m_x1", c_uint),
        ("m_y1", c_uint),
        ("m_index", c_uint),
        ("m_flags", c_uint)]


class IntersectionLine (Structure):
    _fields_ = [
        ("m_index", c_uint),
        ("m_reserved", c_uint),
        ("m_angle", c_uint)]


vectors = pixy.VectorArray(100)
intersections = pixy.IntersectionArray(100)
barcodes = pixy.BarcodeArray(100)
frame = 0


def get_vec():
    pixy.line_get_main_features()
    v_count = pixy.line_get_vectors(100, vectors)
    if v_count > 0:
        for index in range(0, v_count):
            vec = {'vec': [vectors[index].m_x0,
                           -vectors[index].m_y0,
                           vectors[index].m_x1,
                           -vectors[index].m_y1]}
    else:
        vec = {'vec': [np.nan, np.nan, np.nan, np.nan]}
    return vec


def xbar(vec):
    return [vec[2]-vec[0], vec[3]-vec[1]]


def deg2pan(alp):
    # 20 digits = -90 deg
    # 500 digits = 0 deg
    digits = int(500 + 480./90.*alp)
    digits = 20 if digits < 20 else digits
    digits = 980 if digits > 980 else digits
    return digits


class Synchronizer(threading.Thread):
    def __init__(self, task, rec):
        threading.Thread.__init__(self)
        self.task = task
        self.rec = rec
        self.is_running = True

    def kill(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            cyc_time = sum(self.task.task['t'])
            alp = gaitlaw.alpha(*self.task.task['q'])
            torso = (alp[2] if self.rec.recorded['pr2'] >
                     self.rec.recorded['pr3'] else -alp[2])
            self.task.task['run'] = True
            time.sleep(.2*cyc_time)
            self.task.task['run'] = False
            self.task.task['cam'][0] = deg2pan(torso)
            time.sleep(.85*cyc_time)


class PixyThread(threading.Thread):
    def __init__(self, task, rec):
        threading.Thread.__init__(self)
        self.is_running = True
        self.task = task
        self.sync = Synchronizer(task, rec)

        pixy.init()
        pixy.change_prog("line")
        pixy.set_lamp(1, 1)
        time.sleep(.1)
        pixy.set_lamp(0, 0)
        pixy.set_servos(500, 500)
        self.vec = get_vec()

    def run(self):
        self.sync.start()
        while self.is_running:
            pixy.set_servos(self.task.task['cam'][0],
                            self.task.task['cam'][1])
            self.vec = get_vec()
            self.task.task['q'] = gaitlaw.qast_nhorizon(xbar(self.vec))
            time.sleep(.1)

    def kill(self):
        self.sync.kill()
        self.sync.join()
        self.is_running = False
        pixy.set_lamp(0, 0)
