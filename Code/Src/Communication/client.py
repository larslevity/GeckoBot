#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 15:18:21 2018
@author: bianca
"""

import socket
import abc
from subprocess import call
import threading
import time

from Src.Management.thread_communication import imgproc_rec
from Src.Management.thread_communication import ui_state
from Src.Management.thread_communication import llc_ref
from Src.Management import timeout
from Src.Management import exception


try:
    from Src.Communication import pickler
except ImportError:
    print('Relative Import does not work..')


def start_image_capture_server(ip='134.28.136.49'):
    cmd = 'ssh -i ~/.ssh/key_CBoardBBB_main pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/Src/Visual/PiCamera/server.py &'.format(ip)
    call(cmd, shell=True)


def start_img_processing(ip='134.28.136.49'):
    cmd = 'ssh -i ~/.ssh/key_CBoardBBB_main pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/RPi_main.py &'.format(ip)
    call(cmd, shell=True)


def start_img_processing_from_bianca(ip='134.28.136.49'):
    cmd = 'ssh -i ~/.ssh/key_bianca pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/RPi_main.py &'.format(ip)
    call(cmd, shell=True)


def start_liveplotter(ip='134.28.136.70'):
    cmd = 'ssh -i ~/.ssh/key_CBoardBBB_main pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/pc_liveplotter_main.py &'.format(ip)
    call(cmd, shell=True)


def start_UI(ip='192.168.5.2'):
    cmd = 'ssh -i ~/.ssh/key_CBoardBBB_main root@{} nohup python3\
        /root/Git/GeckoBot/Code/UI_main.py &'.format(ip)
    call(cmd, shell=True)


class Socket(object):  # pragma: no cover
    """Base class for Sockets. This defines the interface to Sockets"""
    __metaclass__ = abc.ABCMeta

    def __init__(self, ip):
        self.client_socket = socket.socket()
        self.client_socket.connect((ip, 12397))
        self.connection = self.client_socket.makefile('wb')

    def send_all(self, data):
        self.client_socket.sendall(pickler.pickle_data(data))

    def recieve_data(self):
        ans = pickler.unpickle_data(self.client_socket.recv(4096))
        return ans

    def close(self):
        self.send_all(['Exit'])
        self.connection.close()
        self.client_socket.close()


class LivePlotterSocket(Socket):
    def __init__(self, ip='134.28.136.70'):
        Socket.__init__(self, ip)

    def send_sample(self, sample):
        self.send_all(['sample', sample])
        resp = self.recieve_data()
        return resp


class IMGProcSocket(Socket):
    def __init__(self, ip='134.28.136.49'):
        Socket.__init__(self, ip)

    def get_alpha(self):
        self.send_all(['get_alpha'])
        alpha = self.recieve_data()
        return alpha


class ImgProcReader(threading.Thread):
    def __init__(self, imgprocsock):
        threading.Thread.__init__(self)
        self.is_running = True
        self.imgprocsock = imgprocsock

    def run(self):
        while self.is_running:
            alpha, eps, (X, Y), xref = self.imgprocsock.get_alpha()
            for i in range(len(X)):
                imgproc_rec.X[i] = X[i]
                imgproc_rec.Y[i] = Y[i]
            for i in range(len(alpha)):
                imgproc_rec.aIMG[i] = alpha[i]

            imgproc_rec.eps = eps
            imgproc_rec.xref = xref
            time.sleep(.2)

    def kill(self):
        self.is_running = False
        self.imgprocsock.close()


class CameraSocket(Socket):
    def __init__(self, ip='134.28.136.49'):
        Socket.__init__(self, ip)

    def make_image(self, filename='test', folder='/home/pi/CBoardImgs/',
                   imgformat='.jpg'):
        self.send_all('m{}'.format(folder+filename+imgformat))

    def make_video(self, filename, folder='/home/pi/testimages/',
                   vidformat='.h264'):
        self.send_all('v{}'.format(folder+filename+vidformat))


class UISocket(Socket):
    def __init__(self, ip):
        Socket.__init__(self, ip)
        self.busy = False

    def get_data(self):
        self.send_all(['get'])
        data = self.recieve_data()
        return data

    def select_from_list(self, lis, Q='', time_to_answer=2):
        self.busy = True
        time.sleep(.3)
        self.send_all(['select from list', lis, Q, time_to_answer])
        data = self.recieve_data()
        self.busy = False
        return data

    def select_from_keylist(self, dic, default, time_to_answer=2):
        self.busy = True
        time.sleep(.3)
        self.send_all(['select from keylist', dic, default, time_to_answer])
        data = self.recieve_data()
        self.busy = False
        return data

    def lcd_display(self, msg):
        self.busy = True
        time.sleep(.3)
        self.send_all(['display', msg])
        self.busy = False


class UIReader():
    def __init__(self, ui_sock):
        self.is_running = True
        self.ui_sock = ui_sock

    def run(self):
        while self.is_running:
            if self.ui_sock.busy:
                time.sleep(.2)
            else:
                with timeout.timeout(1):
                    try:
                        ui_state.set_state(self.ui_sock.get_data())
                    except exception.TimeoutError:
                        print('UI doesnt respond')

    def kill(self):
        self.is_running = False
        self.ui_sock.close()


if __name__ == "__main__":
    import pickler

#    start_img_processing_from_bianca()
    start_img_processing()
    time.sleep(5)

    sock = IMGProcSocket()
    time.sleep(1)

    try:
        while True:
            alpha, eps, positions = sock.get_alpha()
            print(alpha)
            print(eps)
            X, Y = positions
            print(X[0], Y[0])
    except KeyboardInterrupt:
        sock.close()
    finally:
        sock.close()
