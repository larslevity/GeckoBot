# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 12:22:00 2019

@author: AmP
"""
import threading
import time

import errno
from socket import error as SocketError


from Src.Visual.GUI import datamanagement as mgmt

from Src.Management.thread_communication import llc_rec
from Src.Management.thread_communication import llc_ref
from Src.Management.thread_communication import imgproc_rec


n_pc = len(llc_rec.p)           # proportional channels
n_dc = len(llc_ref.dvalve)      # discrete channels


def prepare_data():
    p = [round(llc_rec.p[i], 2) for i in range(n_pc)]
    r = [round(llc_ref.pressure[i], 2) for i in range(n_pc)]
    u = [round(llc_rec.u[i], 2) for i in range(n_pc)]
    f = [round(llc_ref.dvalve[i], 2) for i in range(n_dc)]

    aIMG = [round(imgproc_rec.aIMG[i], 2) if imgproc_rec.aIMG[i] else None
            for i in range(8)]
    eps = (round(imgproc_rec.eps, 2) if imgproc_rec.eps else None)
    X = [round(imgproc_rec.X[i], 2) if imgproc_rec.X[i] else None
         for i in range(len(imgproc_rec.X))]
    Y = [round(imgproc_rec.Y[i], 2) if imgproc_rec.Y[i] else None
         for i in range(len(imgproc_rec.Y))]

    rec_angle = llc_rec.aIMU
    aIMU = [round(rec_angle[i], 2) if rec_angle[i] else None
            for i in range(len(llc_rec.aIMU))]

    return (p, r, u, f, aIMG, eps, X, Y, aIMU)


def make_printable(p, r, u, f, aIMG, eps, X, Y, aIMU):
    if len(aIMG) < n_pc:
        aIMG = aIMG + [None]*(n_pc-len(aIMG))
    if len(aIMU) < n_pc:
        aIMU = aIMU + [None]*(n_pc-len(aIMU))
    if len(X) < n_pc:
        X = X + [None]*(n_pc-len(X))
    if len(Y) < n_pc:
        Y = Y + [None]*(n_pc-len(Y))

    return p, r, u, f, aIMG, eps, X, Y, aIMU


class ConsolePrinter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.state = 'RUN'

    def print_state(self):
        p, r, u, f, aIMG, eps, X, Y, aIMU = make_printable(*prepare_data())
        eps = [eps] + [None]*3
        state_str = '\n\t| Ref \t| State \t| epsilon \n'
        state_str = state_str + '-------------------------------------------\n'
        for i in range(4):
            s = '{}\t| {}\t| {} \t\t| {}\n'.format(
                i, f[i], '-', eps[i])
            state_str = state_str + s
        state_str = (
            state_str
            + '\n\t| Ref \t| p \t| PWM \t| aIMU \t| aIMG \t| POS  \n')
        state_str = state_str + '-'*75 + '\n'
        for i in range(n_pc):
            s = '{}\t| {}\t| {}\t| {}\t| {}\t| {}\t| ({},{})\n'.format(
                i, r[i], p[i], u[i], aIMU[i], aIMG[i], X[i], Y[i])
            state_str = state_str + s
        print(state_str)

    def run(self):
        while self.state != 'EXIT':
            self.print_state()
            time.sleep(.2)

    def kill(self):
        self.state = 'EXIT'


class GUIPrinter(threading.Thread):
    def __init__(self, plotsock, IMU=False, IMG=False):
        threading.Thread.__init__(self)

        self.state = 'RUN'
        self.plotsock = plotsock
        self.IMU_connected = True if IMU else False
        self.IMG_connected = True if IMG else False

    def run(self):
        while self.state != 'EXIT':
            if self.plotsock:
                try:
                    sample = mgmt.rehash_record(*prepare_data(),
                                                IMU=self.IMU_connected,
                                                IMG=self.IMG_connected)
                    _ = self.plotsock.send_sample(sample)
                except SocketError as err:
                    if err.errno != errno.ECONNRESET:
                        raise
                    print(err)
                    self.plotsock = None
                time.sleep(.1)

    def kill(self):
        self.state = 'EXIT'
        self.plotsock.close()
