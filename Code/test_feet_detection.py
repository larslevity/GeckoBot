#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 17:01:48 2018

@author: bianca
"""

import time
import cv2
import imutils
from imutils.video import FPS

from Src.Visual.PiCamera.PiVideoStream import PiVideoStream
from Src.Visual import feet_detection as fd


def main(testtime=100, disp=False):

    print("[INFO] warm up the camera sensor...")
    vs = PiVideoStream().start()
    # allow the camera sensor to warmup
    time.sleep(2.0)

    # created a *threaded *video stream, and start the FPS counter
    print("[INFO] sampling THREADED frames from `picamera` module...")

    start = time.time()
    fps = FPS().start()
    # loop over some frames...this time using the threaded stream
    try:
        while time.time()-start < testtime:
            # grab the frame from the threaded video stream and resize it
            # to have a maximum width of 400 pixels
            frame = vs.read()
            frame = imutils.resize(frame, width=400)

            # detect circles
            circs, img = fd.detect_circles(frame)
            print circs

            # check to see if the frame should be displayed to our screen
            if disp:
                if img is not None:
                    cv2.imshow("Frame", img)
                else:
                    cv2.imshow("Frame", frame)
                cv2.waitKey(1) & 0xFF

            fps.update()
    finally:
        vs.stop()
    # stop the timer and display FPS information
    fps.stop()
    cv2.destroyAllWindows()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))


if __name__ == "__main__":
    main(disp=True)
