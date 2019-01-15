# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 16:29:41 2019

@author: AmP
"""



import cv2
import imutils

import apriltag
import numpy as np


# from Src.Visual import feet_detection as fd
from Src.Math import IMUcalc
from Src.Math import kinematic_model_fun as kin_mod


def calc_robo_repr(frame, disp=True):
    detector = apriltag.Detector()

    frame = imutils.resize(frame, width=700)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detect circles
    april_result = detector.detect(frame)

    img = mask_img(frame, april_result)
#    img = frame

    # check to see if the frame should be displayed to our screen
    if disp:
        if img is not None:
            cv2.imshow("Frame", img)
        else:
            cv2.imshow("Frame", frame)
        cv2.waitKey(0)
#        cv2.waitKey(1) & 0xFF

#    cv2.destroyAllWindows()


def mask_img(img, april_result):
    if april_result is not None:
        bend_angle, eps = calc_angle(april_result)
        X, Y = extract_positions(april_result)

        #print bend_angle

        pattern = [[bend_angle[idx] for idx in [0, 1, 2, 4, 5]], [0, 1, 0, 0]]
        pose = [pattern[0], eps, (X[0], Y[0])]
        #print pose
        x, r, (data, data_fp, data_nfp, data_x), costs = kin_mod.predict_pose([pattern], pose)
        
        
        img = mask_repr(img, data[-1])

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
    for x, y in zip(X, Y):
        cv2.circle(img, (int(x), int(y)), 1, (255, 255, 255))
    return img

        
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
    frame = cv2.imread('photo_2019-01-15--14-39-58.jpg', 1)

    calc_robo_repr(frame, disp=True)
