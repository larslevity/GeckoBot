# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 16:06:15 2018

@author: AmP
"""

#if __name__ == "__main__":
from __future__ import print_function

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import cv2


class PiVideoStream:
    def __init__(self, resolution=(640, 480), framerate=32):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr",
                                                     use_video_port=True)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


if __name__ == "__main__":
    # import the necessary packages

    from imutils.video import FPS

    import argparse
    import imutils
    import time

    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--num-frames", type=int, default=100,
                    help="# of frames to loop over for FPS test")
    ap.add_argument("-d", "--display", type=int, default=-1,
                    help="Whether or not frames should be displayed")
    args = vars(ap.parse_args())

    # initialize the camera and stream
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))
    stream = camera.capture_continuous(rawCapture, format="bgr",
                                       use_video_port=True)

    # allow the camera to warmup and start the FPS counter
    print("[INFO] sampling frames from `picamera` module...")
    time.sleep(2.0)
    fps = FPS().start()

    # loop over some frames
    for (i, f) in enumerate(stream):
        # grab the frame from the stream and resize it to have a maximum
        # width of 400 pixels
        frame = f.array
        frame = imutils.resize(frame, width=700)

        # check to see if the frame should be displayed to our screen
        if args["display"] > 0:
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF
     
        # clear the stream in preparation for the next frame and update
        # the FPS counter
        rawCapture.truncate(0)
        fps.update()

        # check to see if the desired number of frames have been reached
        if i == args["num_frames"]:
            break

    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    # do a bit of cleanup
    cv2.destroyAllWindows()
    stream.close()
    rawCapture.close()
    camera.close()

    # created a *threaded *video stream, allow the camera sensor to warmup,
    # and start the FPS counter
    print("[INFO] sampling THREADED frames from `picamera` module...")
    vs = PiVideoStream().start()
    time.sleep(2.0)
    fps = FPS().start()

    # loop over some frames...this time using the threaded stream
    while fps._numFrames < args["num_frames"]:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=700)

        # check to see if the frame should be displayed to our screen
        if args["display"] > 0:
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

        # update the FPS counter
        fps.update()

    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()
