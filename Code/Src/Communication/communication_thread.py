# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 14:24:30 2017

@author: ls
"""
from __future__ import print_function

import __builtin__
import socket
import sys
import threading
import traceback
import time

from termcolor import colored
from Src.Communication import pickler
from Src.Controller import controller as ctrlib


def print(*args, **kwargs):
    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


class CommunicationThread(threading.Thread):
    def __init__(self, cargo):
        """ """
        threading.Thread.__init__(self)
        self.cargo = cargo
        self.SOCK = None
        self.connection = None

        print('Starting server ...')
        self.SOCK = init_connection()

    def run(self):
        """ run the Communication """

        print('Waiting for connection')
        self.connection, client_adress = self.SOCK.accept()
        print('Sucessfull connected to ', client_adress)

        try:
            while self.cargo.state != 'EXIT':
                try:
                    self.get_tasks()
                except:
                    print('\n--caught exception! in Communictaion Thread--\n')
                    print("Unexpected error:\n", sys.exc_info()[0])
                    print(sys.exc_info()[1])
                    traceback.print_tb(sys.exc_info()[2])
                    print('\nBreaking the communication loop ...')
                    break
        finally:
            print('Exit the communication Thread ...')
            self.cargo.state = 'EXIT'
            graceful_exit(self.connection, self.SOCK)

        print('Communication Thread is done ...')

    def get_tasks(self):
        data_in_raw = self.connection.recv(4096)
        data_in_list = pickler.unpickle_data(data_in_raw)

        for data_in in data_in_list:
            if 'update' in data_in:
                self.send_back([self.cargo.rec, self.cargo.rec_u,
                                self.cargo.rec_r])

            if 'valve_meta_info' in data_in:
                valve_data = []
                for valve in self.cargo.valve:
                    valve_data.append(valve.name)
                PID_gains = []
                for c in self.cargo.controller:
                    PID_gains.append([c.Kp, c.Ti, c.Td])
                self.send_back([valve_data,
                                self.cargo.maxpressure,
                                self.cargo.maxctrout,
                                self.cargo.sampling_time,
                                PID_gains,
                                self.cargo.wcomm.pattern])

            if 'dvalve_meta_info' in data_in:
                dvalve_data = []
                for dvalve in self.cargo.dvalve:
                    dvalve_data.append(dvalve.name)
                self.send_back(dvalve_data)

            if 'change_state' in data_in:
                candidates = ['PAUSE', 'REFERENCE_TRACKING', 'EXIT',
                              'USER_CONTROL', 'USER_REFERENCE']
                new_state = None
                for candidate in candidates:
                    if candidate in data_in:
                        new_state = candidate
                        print('recieved task to change state to:', new_state)
                if new_state:
                    self.cargo.state = new_state
                    while not self.cargo.actual_state == new_state:
                        time.sleep(self.cargo.sampling_time)
                self.send_back(new_state)

            if 'set_valve' in data_in:
                valve_data = data_in[1]
                for key in valve_data:
                    self.cargo.pwm_task[key] = valve_data[key]

            if 'set_ref' in data_in:
                ref_data = data_in[1]
                for key in ref_data:
                    self.cargo.ref_task[key] = ref_data[key]

            if 'set_dvalve' in data_in:
                dvalve_data = data_in[1]
                for key in dvalve_data:
                    self.cargo.dvalve_task[key] = dvalve_data[key]

            if 'set_pidgain' in data_in:
                idx = data_in[1]
                gain_data = data_in[2]
                if isinstance(self.cargo.controller[idx],
                              ctrlib.PidController):
                    self.cargo.controller[idx].set_gain(gain_data)
                else:
                    raise NotImplementedError(
                        "Controller", self.cargo.controller[idx],
                        "doesn't support gain setting at runtime")
                c = self.cargo.controller[idx]
                gain = [c.Kp, c.Ti, c.Td]
                self.send_back(gain)

            if 'set_maxpressure' in data_in:
                maxpressure = data_in[1]
                if 10 > maxpressure > 0:
                    self.cargo.maxpressure = maxpressure
                    for sensor in self.cargo.sens:
                        sensor.set_maxpressure(maxpressure)
                self.send_back(self.cargo.maxpressure)

            if 'set_maxctrout' in data_in:
                maxctrout = data_in[1]
                if 1. > maxctrout > 0.:
                    self.cargo.maxctrout = maxctrout
                    for ctr in self.cargo.controller:
                        ctr.set_maxoutput(maxctrout)
                self.send_back(self.cargo.maxctrout)

            if 'set_tsampling' in data_in:
                tsampling = data_in[1]
                if 1. > tsampling > 0.:
                    self.cargo.sampling_time = tsampling
                self.send_back(self.cargo.sampling_time)

            if 'set_pattern' in data_in:
                pattern = data_in[1]
                self.cargo.wcomm.pattern = pattern
                self.send_back(self.cargo.wcomm.pattern)

            if 'set_walking' in data_in:
                state = data_in[1]
                self.cargo.wcomm.confirm = state
                self.send_back(self.cargo.wcomm.confirm)

    def send_back(self, data_out):
        data_out_raw = pickler.pickle_data(data_out)
        self.connection.sendall(data_out_raw)


def init_connection():
    HOST = None               # Symbolic name meaning all available interfaces
    PORT = 10000              # Arbitrary non-privileged port
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC,
                                  socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
            print('socket created with address family: ', af)
        except socket.error as msg:
            print('error while creating socket: ', msg)
            s = None
            continue
        try:
            s.bind(sa)
            s.listen(100)
            print('socket bounded with server address: ', sa)
        except socket.error as msg:
            s.close()
            s = None
            print('Error while sock.bind: ', msg)
            continue
        break
    if s is None:
        print('could not open socket')
        sys.exit(1)
    SOCK = s
    return SOCK


def graceful_exit(connection, SOCK):
    """Shutdown"""
    print('Closing Socket ...')
    SOCK.close()
    print('Closing Connection ...')
    connection.close()
