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

try:
    from Src.Visual.PiCamera import pickler
except ImportError:
    print('Relative Import does not work..')


def start_server(ip='134.28.136.49'):
    cmd = 'ssh -i ~/.ssh/BBB_key pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/Src/Visual/PiCamera/server.py &'.format(ip)
    call(cmd, shell=True)


def start_img_processing(ip='134.28.136.49'):
    cmd = 'ssh -i ~/.ssh/BBB_key pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/RPi_main.py &'.format(ip)
    call(cmd, shell=True)


def start_img_processing_from_bianca(ip='134.28.136.49'):
    cmd = 'ssh -i ~/.ssh/key_bianca pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/RPi_main.py &'.format(ip)
    call(cmd, shell=True)


def start_liveplotter(ip='134.28.136.70'):
    cmd = 'ssh -i ~/.ssh/BBB_key pi@{} nohup python\
        /home/pi/Git/GeckoBot/Code/pc_liveplotter_main.py &'.format(ip)
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


class CameraSocket(Socket):
    def __init__(self, ip='134.28.136.49'):
        Socket.__init__(self, ip)

    def make_image(self, filename='test', folder='/home/pi/CBoardImgs/',
                   imgformat='.jpg'):
        self.send_all('m{}'.format(folder+filename+imgformat))

    def make_video(self, filename, folder='/home/pi/testimages/',
                   vidformat='.h264'):
        self.send_all('v{}'.format(folder+filename+vidformat))


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

#    sock = ClientSocket()
#    for foo in range(3):
#        sock.get_image('image{}'.format(foo))
#        time.sleep(2)
#        sock.close()
