#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 15:19:41 2018

@author: bianca
"""

import io
import socket
import struct
import time
import picamera

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
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
            if task[0] == 'm':  # make photo and save to PI
                filename = task[1:]
                camera.capture(filename)
            # Reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
    # Write a length of zero to the stream to signal we're done
    connection.write(struct.pack('<L', 0))
finally:
    connection.close()
    server_socket.close()