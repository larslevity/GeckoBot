# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 16:29:41 2019

@author: mustapha


IMG -> (detect_apriltags) -> aprilresult
aprilresult -> (extract_position) -> fpos, tpos
aprilresult -> (extract_alpha) -> alpha, eps
fpos, tpos, alpha, eps -> (calc_pose) -> pose

"""

import cv2

import apriltag
import numpy as np

from Src.Math import IMUcalc
from Src.Math import kinematic_model_fun as kin_mod


detector = apriltag.Detector()


def detect_all(frame):
    april_result = detect_apriltags(frame)
    # extract pose
    if len(april_result) > 0:
        alpha, eps = extract_alpha(april_result)
        X, Y, xref = extract_position(april_result)
    else:
        alpha, eps = None, None
        X, Y = None, None
        xref = None

    return alpha, eps, (X, Y), xref


def calc_pose(alpha, eps, positions):
    alpha_ = alpha[0:3] + alpha[4:6]
    pose_coords, ell, bet = kin_mod.extract_pose(alpha_, eps, positions)
    return pose_coords, ell, bet


def detect_apriltags(frame):
    # gray frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detect apriltags
    april_result = detector.detect(frame)
    return april_result


def extract_position(april_result):
    SHIFT = {
        0: [0, 1, 10],
        1: [0, 3, 16],
        2: [1, 0, 10],
        3: [0, 1, 10],
        4: [3, 0, 5],
        5: [1, 0, 10],
            }
    X, Y = [None]*6, [None]*6
    xref = (None, None)
    for res in april_result:
        tag_id = res.tag_id
        if tag_id == 6:
            xref = (int(res.center[0]), int(res.center[1]))
        else:
            pc0 = np.array([res.corners[SHIFT[tag_id][0]][0],
                            res.corners[SHIFT[tag_id][0]][1]])
            pc1 = np.array([res.corners[SHIFT[tag_id][1]][0],
                            res.corners[SHIFT[tag_id][1]][1]])
            shift = (pc1-pc0)/np.linalg.norm(pc1-pc0)*SHIFT[tag_id][2]
            center = res.center + shift
            x, y = int(center[0]), int(center[1])
            X[tag_id] = x
            Y[tag_id] = y
    return X, Y, xref


def extract_alpha(april_result):
    jump = np.pi/180.*70  # jump bei 110
    POSs = {
            0: [0, 1],
            1: [1, 2],
            2: [1, 4],
            3: [4, 1],
            4: [4, 3],
            5: [5, 4]
            }
    ori = [None]*6
    center = []
    for res in april_result:
        tag_id = res.tag_id
        if tag_id < 6:
            ori[tag_id] = res.corners[2] - res.corners[0]
            if tag_id == 1 or tag_id == 4:
                center.append(res.center)

    angle, eps = [None]*6, None
    for tag_id in POSs:
        if ori[POSs[tag_id][0]] is not None and ori[POSs[tag_id][1]] is not None:
            p0, p1 = (np.append(ori[POSs[tag_id][0]], 0),
                      np.append(ori[POSs[tag_id][1]], 0))

            angle[tag_id] = round(IMUcalc.calc_angle(p0, p1, jump=jump), 1)

    # calc eps
    if len(center) == 2:
        p0, p1 = np.append(center[0], 0), np.append(center[1], 0)
        eps = np.mod(-round(IMUcalc.calc_angle(p1-p0, [1, 0, 0]) + 180, 1), 360)

    return angle, eps


def draw_positions(img, position_coords):
    X, Y = position_coords
    for tag_id, coords in enumerate(zip(X, Y)):
        x, y = coords
        if x is not None:
            cv2.rectangle(img, (x-5, y-5), (x+5, y+5), (0, 128, 255), -1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontscale = .8
            col = (255, 0, 0)
            cv2.putText(img, str(tag_id), (x, y-10), font, fontscale, col, 2)

    return img


def draw_rects(img):
    april_result = detect_apriltags(img)
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontscale = .8
    col = (255, 0, 0)
    for res in april_result:
        tag_id = res.tag_id
        xc, yc = int(res.center[0]), int(res.center[1])
        cv2.putText(img, str(tag_id), (xc, yc), font, fontscale, col, 2)
        for corner in range(4):
            x, y = int(res.corners[corner][0]), int(res.corners[corner][1])
            cv2.putText(img, str(corner), (x, y), font, fontscale*.5, col, 2)
    return img


def draw_pose(img, pose_coords):
    (X, Y) = pose_coords
    for x, y in zip(X, Y):
        cv2.circle(img, (int(x), int(y)), 1, (255, 255, 255))
    return img
