# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 16:29:41 2019

@author: mustapha
"""



import cv2
import imutils

import apriltag
import numpy as np


# from Src.Visual import feet_detection as fd
from Src.Math import IMUcalc
from Src.Math import kinematic_model_fun as kin_mod


def calc_robo_repr(frame):
    detector = apriltag.Detector()
    # fit frame
    frame = imutils.resize(frame, width=700)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detect apriltags
    april_result = detector.detect(frame)

    # detect pose
    if len(april_result) == 6:
        bend_angle, eps = calc_angle(april_result)
        bend_angle = bend_angle[0:3] + bend_angle[4:6]
        X, Y = extract_positions(april_result)
        
        print bend_angle

        print eps
        (xa, ya), ell, bet = kin_mod.extract_pose(bend_angle, eps, (X, Y))

        img = mask_img(frame, april_result, (xa, ya))
    else:
        img = frame

    return img


def mask_img(img, april_result, (xa, ya)):

    img = mask_repr(img, (xa, ya))

    for res in april_result:
        tag_id = res.tag_id
        x, y = int(res.center[0]), int(res.center[1])

        cv2.rectangle(img, (x-5, y-5), (x+5, y+5), (0, 128, 255), -1)
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontscale = .8
        col = (255, 0, 0)
        cv2.putText(img, str(tag_id), (x, y-10), font, fontscale, col, 2)

    return img


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
            'eps': [4, 1]
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
                eps = -round(IMUcalc.calc_angle(p1+p0, [1, 0, 0]), 1) + 135.
            else:
                angle[tag_id] = round(IMUcalc.calc_angle(p0, p1), 1)

    return angle, eps
