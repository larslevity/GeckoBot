# -*- coding: utf-8 -*-
"""
Created on Tue Nov 06 15:44:41 2018

@author: AmP
"""

import io
import socket
import struct
import time
import picamera

STREAM = False

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
conn = server_socket.accept()[0]
connection = conn.makefile('rb')


if STREAM:
    try:
        with picamera.PiCamera() as camera:
            camera.resolution = (2592, 1944)
            # Start a preview and let the camera warm up for 2 seconds
            camera.start_preview()
            time.sleep(2)

            # Note the start time and construct a stream to hold image data
            # temporarily (we could write it directly to connection but in this
            # case we want to find out the size of each capture first to keep
            # our protocol simple)

            stream = io.BytesIO()
            for foo in camera.capture_continuous(stream, 'jpeg'):
                # Write the length of the capture to the stream and flush to
                # ensure it actually gets sent
                connection.write(struct.pack('<L', stream.tell()))
                connection.flush()
                # Rewind the stream and send the image data over the wire
                stream.seek(0)
                connection.write(stream.read())
                # If we've been capturing for more than 30 seconds, quit
                task = conn.recv(4096)
                if task == 'Exit':
                    break
                # Reset the stream for the next capture
                stream.seek(0)
                stream.truncate()
        # Write a length of zero to the stream to signal we're done
        connection.write(struct.pack('<L', 0))
    finally:
        connection.close()
        server_socket.close()
else:
    try:
        with picamera.PiCamera() as camera:
            camera.resolution = (2592, 1944)
            # Start a preview and let the camera warm up for 2 seconds
            camera.start_preview()
            time.sleep(2)

            while True:
                task = conn.recv(4096)
                if task[0] == 'm':
                    filename = task[1:]
                    camera.capture(filename)
                if task[0] == 'v':
                    filename = task[1:]
                    camera.resolution = (640, 480)
                    camera.start_recording(filename)
                    camera.wait_recording(2)
                    camera.stop_recording()
    finally:
        connection.close()
server_socket.close()