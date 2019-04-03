# -*- coding: utf-8 -*-
"""
Created on Tue Nov 06 15:44:41 2018

@author: AmP
"""


import socket

import time
import picamera

import pickler


# Start a socket listening for connections on 0.0.0.0:8000
server_socket = socket.socket()
server_socket.bind(('', 12397))  # (0.0.0.0 means all interfaces)
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
conn = server_socket.accept()[0]
connection = conn.makefile('rb')


try:
    with picamera.PiCamera() as camera:
        camera.resolution = (2592, 1944)
        # Start a preview and let the camera warm up for 2 seconds
        camera.start_preview()
        time.sleep(2)
        i = 0
        while True:
            task_raw = conn.recv(4096)
            task = pickler.unpickle_data(task_raw)
            if task[0] == 'm':
                filename = task[1:]
                camera.capture(filename)
            if task[0] == 'v':
                filename = task[1:]
                camera.resolution = (640, 480)
                camera.start_recording(filename.split('.')[0]+str(i).zfill(2)+'.h264')
                camera.wait_recording(60)
                camera.stop_recording()
                i += 1
finally:
    connection.close()

server_socket.close()
