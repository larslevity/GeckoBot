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
import apriltag
import numpy as np

from Src.Visual.PiCamera.PiVideoStream import PiVideoStream
# from Src.Visual import feet_detection as fd
from Src.Math import IMUcalc
from Src.Math import kinematic_model_fun as kin_mod




def main(testtime=200, disp=False):

#    print("[INFO] warm up the camera sensor...")
#    vs = PiVideoStream().start()
#    # allow the camera sensor to warmup
#    time.sleep(2.0)
#
#    # created a *threaded *video stream, and start the FPS counter
#    print("[INFO] detect green dots...")
#
#    start = time.time()
#    fps = FPS().start()
#    # loop over some frames...this time using the threaded stream
#    try:
#        while time.time()-start < testtime:
#            # grab the frame from the threaded video stream and resize it
#            # to have a maximum width of 400 pixels
#            frame = vs.read()
#            frame = imutils.resize(frame, width=400)
#
#            # detect circles
#            circs, img = fd.detect_circles(frame)
#            #print circs
#
#            # check to see if the frame should be displayed to our screen
#            if disp:
#                if img is not None:
#                    cv2.imshow("Frame", img)
#                else:
#                    cv2.imshow("Frame", frame)
#                cv2.waitKey(1) & 0xFF
#
#            fps.update()
#    finally:
#        vs.stop()
#    # stop the timer and display FPS information
#    fps.stop()
#    cv2.destroyAllWindows()
#    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
#    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    ##########################################################################

    print("[INFO]detect april tags...")
    detector = apriltag.Detector()

    vs = PiVideoStream(resolution=(640, 480)).start()
    # allow the camera sensor to warmup
    time.sleep(2.0)

    start = time.time()
    fps = FPS().start()
    try:
        while time.time()-start < testtime:
            # grab the frame from the threaded video stream and resize it
            # to have a maximum width of 400 pixels
            frame = vs.read()
            frame = imutils.resize(frame, width=700)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # detect circles
            april_result = detector.detect(frame)

            img = mask_img(frame, april_result)

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

    fps.stop()
    cv2.destroyAllWindows()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))



def mask_img(img, april_result):
    if april_result is not None:
        bend_angle, eps = calc_angle(april_result)
        X, Y = extract_positions(april_result)
        
        print bend_angle

        pattern = [[bend_angle[idx] for idx in [0, 1, 2, 4, 5]], [1, 1, 1, 1]]
        pose = [pattern[0], eps, (X[0], Y[0])]
        print pose
        x, r, data_, cst = kin_mod.predict_pose([pattern], pose)
        data, data_fp, data_nfp, data_x = data_
        mask_repr(data, img)
        
        for res in april_result:
            tag_id = res.tag_id
            x, y = int(res.center[0]), int(res.center[1])
    
            cv2.rectangle(img, (x-5, y-5), (x+5, y+5), (0, 128, 255), -1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontscale = .8
            col = (255, 0, 0)
            cv2.putText(img, str(tag_id), (x, y-10), font, fontscale, col, 2)
    
        return img
    else:
        return None


def mask_repr(img, data):
    (X, Y) = data
    for x,y in zip(X, Y):
        cv2.circle(img, (int(x), int(y)), 1, (0, 128, 255))

        

def extract_positions(april_result):
    X, Y = [None]*6, [None]*6
    for res in april_result:
        tag_id = res.tag_id
        x, y = int(res.center[0]), int(res.center[1])
        X[tag_id] = x
        Y[tag_id] = y
    return X, Y
    

def calc_angle(april_result):
    POSs = {
    0: [0, 1],
    1: [1, 2],
    2: [1, 4],
    3: [4, 1],
    4: [4, 3],
    5: [5, 4],
    'eps': [1, 4]
    }
    ori = [None]*6
    for res in april_result:
        tag_id = res.tag_id
        ori[tag_id] = res.corners[2] - res.corners[0] 
    
    angle, eps = [None]*6, None
    for tag_id in POSs:
        if ori[POSs[tag_id][0]] is not None and ori[POSs[tag_id][1]] is not None:
            p0, p1 = (np.append(ori[POSs[tag_id][0]], 0),
                      np.append(ori[POSs[tag_id][1]], 0))
            if tag_id == 'eps':
                eps = round(IMUcalc.calc_angle(p1-p0, [1, 0, 0]), 1)
            else:
                angle[tag_id] = round(IMUcalc.calc_angle(p0, p1), 1)
    
    return angle, eps





if __name__ == "__main__":
    main(disp=True)
