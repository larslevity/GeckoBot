#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 16:52:37 2019

@author: mustapha
"""


import socket
import time
import threading
import errno
import logging
import picamera

from Src.Visual.PiCamera import pickler
from Src.Hardware import rpi_imu
from Src.Math import IMUcalc


logPath = "log/"
fileName = 'rpilog'
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)



IMUset = {
    0: {'id': 0},
    1: {'id': 1},
    2: {'id': 2},
    3: {'id': 3}
    }
CHANNELset = {
    0: {'IMUs': [0, 1], 'IMUrot': 0},
    1: {'IMUs': [2, 3], 'IMUrot': 0}
    }


def init_IMU():
    # mplx address for IMU is 0x71
    try:
        IMU = {}
        for name in IMUset:
            IMU[name] = rpi_imu.GY_521(plx_id=IMUset[name]['id'], name=name)
    except IOError:  # not connected
        IMU = False
        rootLogger.exception('IMUs not found')
    return IMU


def main(memory):

    IMU = init_IMU()

    def read_imu(memory):
        for name in IMU:
            try:
                memory.rec_IMU[name] = IMU[name].get_acceleration()
            except IOError as e:
                if e.errno == errno.EREMOTEIO:
                    rootLogger.exception(
                        'cant read imu device.' +
                        'Continue anyway ...Fail in [{}]'.format(name))
                else:
                    rootLogger.exception('Sensor [{}]'.format(name))
                    raise e
        return memory

    def measure_angle(memory):
        if IMU:
            memory = read_imu(memory)
            for name in CHANNELset:
                idx0, idx1 = CHANNELset[name]['IMUs']
                rot_angle = CHANNELset[name]['IMUrot']
                acc0 = memory.rec_IMU[idx0]
                acc1 = memory.rec_IMU[idx1]
                sys_out = IMUcalc.calc_angle(acc0, acc1, rot_angle)
                memory.rec_angle[name] = round(sys_out, 2)
                #print(name, ':\t', sys_out)
        return memory


    while not memory.exit_flag:
        # read IMUs
        memory = measure_angle(memory)
        time.sleep(.5)
        


class RPi_CameraThread(threading.Thread):
    def __init__(self, memory):
        """ """
        threading.Thread.__init__(self)
        self.memory = memory
        self.exit_flag = False

    def run(self):
        try:
            with picamera.PiCamera() as camera:
                camera.resolution = (2592, 1944)
                # Start a preview and let the camera warm up for 2 seconds
                camera.start_preview()
                time.sleep(2)
                while not self.exit_flag:
                    task = memory.camera_task
                    if task[0] == 'm':
                        camera.resolution = (2592, 1944)
                        filename = task[1:]
                        camera.capture(filename)
                        rootLogger.info('captured image:\t{}'.format(filename))
                        self.memory.camera_task = 'done'
                    if task[0] == 'v':
                        filename = task[1:]
                        camera.resolution = (640, 480)
                        camera.start_recording(filename)
                        camera.wait_recording(10)
                        camera.stop_recording()
                        rootLogger.info('recorded video:\t{}'.format(filename))
                        self.memory.camera_task = 'done'
                    time.sleep(.1)
        except Exception as err:
            rootLogger.error(err, exc_info=True)

    def kill(self):
        self.exit_flag = True


class RPi_CommThread(threading.Thread):
    def __init__(self, connection, memory):
        """ """
        threading.Thread.__init__(self)
        self.connection = connection
        self.memory = memory
        self.exit_flag = False

    # COMM
    def run(self):
        try:
            while not self.exit_flag :
                task_raw = self.connection.recv(4096)
                task = pickler.unpickle_data(task_raw)
                if task[0] == 'get_alpha':
                    self.send_back(self.memory.get_alpha())
                if task[0] in ['m', 'v']:
                    self.memory.camera_task = task
                if task[0] == 'Exit':
                    self.kill()
                    self.memory.kill_main()
        except Exception as err:
            rootLogger.error(err, exc_info=True)
                
    def send_back(self, data_out):
        data_out_raw = pickler.pickle_data(data_out)
        self.connection.sendall(data_out_raw)

    def kill(self):
        self.exit_flag = True


class Memory(object):
    def __init__(self):
        self.rec_IMU = {name: None for name in IMUset}
        self.rec_angle = {name: None for name in CHANNELset}
        self.camera_task = 'done'
        self.exit_flag = False

    def get_alpha(self):
        return [self.rec_angle[name] for name in CHANNELset]
    
    def kill_main(self):
        self.exit_flag = True


if __name__ == '__main__':
#    import sys, traceback

    # Start a socket listening for connections on 0.0.0.0:12397
    server_socket = socket.socket()
    server_socket.bind(('', 12397))
    server_socket.listen(0)
    
    # Accept a single connection and make a file-like object out of it
    conn = server_socket.accept()[0]
    connection = conn.makefile('rb')

    # initialize shared memory    
    memory = Memory()
    # Initialize and run Comm Thread
    comm_thread = RPi_CommThread(conn, memory)
    comm_thread.setDaemon(True)
    comm_thread.start()

    # Initialize and run Comm Thread
    cam_thread = RPi_CameraThread(memory)
    cam_thread.setDaemon(True)
    cam_thread.start()

    try:
        main(memory)
    except Exception as err:
        rootLogger.error(err, exc_info=True)
    finally:
        connection.close()
        comm_thread.kill()
        cam_thread.kill()
        server_socket.close()
