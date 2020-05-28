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

if __name__ == '__main__':
    path2git = path.dirname(path.dirname(path.dirname(path.dirname(
            path.dirname(path.abspath(__file__))))))
    path2src = path.dirname(path.dirname(
            path.dirname(path.abspath(__file__))))
    sys.path.insert(0, path2src)

sys.path.insert(0, path2git)  # insert Git folder into path

from pixy2.build.python_demos import pixy
from Src.Controller import gait_law_planner as gaitlaw

import pyudev


def check_pixy_connect():    
    context = pyudev.Context()
    for device in context.list_devices(subsystem='usb'):
        vendor_id = device.get('ID_VENDOR_ID')
        if vendor_id == 'b1ac':
            print('found pixy')
            return True
        #    print(vendor_id, '\n')
    return False




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
                           206-vectors[index].m_y0,
                           vectors[index].m_x1,
                           206-vectors[index].m_y1]}
    else:
        vec = {'vec': [np.nan, np.nan, np.nan, np.nan]}
    return vec


def xbar(vec):
    return [vec[3]-vec[1], -(vec[2]-vec[0])]


def deg2pan(alp):
    # 20 digits = -90 deg
    # 500 digits = 0 deg
    digits = int(500 + 480./90.*alp)
    digits = 20 if digits < 20 else digits
    digits = 980 if digits > 980 else digits
    return digits


class Synchronizer(threading.Thread):
    def __init__(self, parent, rec):
        threading.Thread.__init__(self)
        self.parent = parent
        self.rec = rec
        self.is_running = True
        self.steps = 30

    def kill(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            if self.parent.task.task['start']:
                # cam ctr
                cyc_time = sum(self.parent.task.task['t'])
                q1, q2 = self.parent.task.task['q']
                sign = (1 if self.rec.recorded['pr2']['val'][-1] <
                         self.rec.recorded['pr3']['val'][-1] else -1)
                torso = gaitlaw.alpha(q1*sign, q2)[2]
                
                self.parent.task.task['run'] = True
                time.sleep(.1*cyc_time)
                self.parent.task.task['run'] = False
                if self.parent.task.task['autocam']:
                    for pan in np.linspace(self.parent.task.task['cam'][0],
                                           deg2pan(torso/2), self.steps):
                        self.parent.task.task['cam'][0] = int(pan)
                        time.sleep(.7*cyc_time/self.steps)
                else:
                    time.sleep(.7*cyc_time)
                time.sleep(.2*cyc_time)
            else:
                time.sleep(.1)

#            print('detect vec...')
#            if np.isnan(self.parent.vec['vec'][0]):
#                self.parent.task.task['q'] = [0, 0]
#                print('no detection!')
#            else:
#                xbar_ = xbar(self.parent.vec['vec'])
#                print('xbar: ', xbar_)
#                self.parent.task.task['q'] = gaitlaw.qast_nhorizon(xbar_)
#            print('q ref:', self.parent.task.task['q'])
                



class PixyThread(threading.Thread):
    def __init__(self, task, rec):
        threading.Thread.__init__(self)
        self.is_running = True
        self.task = task
        self.is_connected = check_pixy_connect()
        if self.is_connected:
            pixy.init()
            pixy.change_prog("line")
            pixy.set_lamp(1, 1)
            time.sleep(.1)
            pixy.set_lamp(0, 0)
            pixy.set_servos(500, 500)
            self.vec = get_vec()
            self.sync = Synchronizer(self, rec)
            self.is_connected = True
        else:
            print('no connection to pixy...')
            self.vec = {'vec': [np.nan, np.nan, np.nan, np.nan]}

    def run(self):
        if self.is_connected:
            self.sync.start()
            while self.is_running:
                pixy.set_servos(self.task.task['cam'][0],
                                self.task.task['cam'][1])
                self.vec = get_vec()
                time.sleep(.1)

    def kill(self):
        if self.is_connected:
            self.sync.kill()
            self.sync.join()
            pixy.set_lamp(0, 0)
        self.is_running = False


if __name__ == '__main__':
    pthread = PixyThread(None, None)
