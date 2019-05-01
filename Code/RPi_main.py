#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 16:52:37 2019

@author: mustapha
"""


import socket
import time
import threading
import cv2

from Src.Visual.PiCamera import IMGprocessing as img_proc
from Src.Visual.PiCamera.PiVideoStream import PiVideoStream
from Src.Visual.PiCamera import pickler


def main(alpha_memory):
#    print("[INFO] warm up camera sensor...")
    vs = PiVideoStream(resolution=(640, 480)).start()
    # allow the camera sensor to warmup
    time.sleep(1.0)
#    print("[INFO] start detect april tags...")

    try:
        while not alpha_memory.exit_flag:
            # grab the frame from the threaded video stream
            frame = vs.read()
            # detect pose
            alpha, eps, positions, xref = img_proc.detect_all(frame)

            if alpha is not None:
                alpha_memory.set_alpha(alpha)
                alpha_memory.set_eps(eps)
                alpha_memory.set_positions(positions)
                alpha_memory.set_xref(xref)
#                img = img_proc.draw_positions(frame, positions)
#            else:
#                img = frame

#            cv2.imshow("Frame", img)
#            cv2.waitKey(1) & 0xFF
    finally:
        vs.stop()

    cv2.destroyAllWindows()


class RPi_CommThread(threading.Thread):
    def __init__(self, connection, alpha_memory):
        """ """
        threading.Thread.__init__(self)
        self.connection = connection
        self.alpha_memory = alpha_memory
        self.exit_flag = False

    # COMM
    def run(self):
        while not self.exit_flag:
            task_raw = self.connection.recv(4096)
            task = pickler.unpickle_data(task_raw)
            if task[0] == 'get_alpha':
                self.send_back([self.alpha_memory.get_alpha(),
                                self.alpha_memory.get_eps(),
                                self.alpha_memory.get_positions(),
                                self.alpha_memory.get_xref()])
            if task[0] == 'Exit':
                self.kill()
                self.alpha_memory.kill_main()

    def send_back(self, data_out):
        data_out_raw = pickler.pickle_data(data_out)
        self.connection.sendall(data_out_raw)

    def kill(self):
        self.exit_flag = True


class Alpha_Memory(object):
    def __init__(self):
        self.alpha = [None]*6
        self.eps = None
        self.fpos = ([None]*6, [None]*6)
        self.exit_flag = False
        self.xref = (None, None)

    def kill_main(self):
        self.exit_flag = True

    def get_alpha(self):
        return self.alpha

    def get_eps(self):
        return self.eps

    def get_xref(self):
        return self.xref

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_eps(self, eps):
        self.eps = eps

    def set_xref(self, xref):
        self.xref = xref

    def set_positions(self, positions):
        self.fpos = positions

    def get_positions(self):
        return self.fpos


if __name__ == '__main__':
#    import sys, traceback

    # Start a socket listening for connections on 0.0.0.0:8000
    server_socket = socket.socket()
    server_socket.bind(('', 12397))
    server_socket.listen(0)

    # Accept a single connection and make a file-like object out of it
    conn = server_socket.accept()[0]
    connection = conn.makefile('rb')

    # initialize shared memory
    alpha_memory = Alpha_Memory()
    # Initialize and run Comm Thread
    comm_thread = RPi_CommThread(conn, alpha_memory)
    comm_thread.setDaemon(True)
    comm_thread.start()

    try:
        main(alpha_memory)
#    except Exception as err:
#        print 'ERROR:'
#        traceback.print_exc(file=sys.stdout)
    finally:
        connection.close()
        comm_thread.kill()
        server_socket.close()
