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

#from Src.Math import kinematic_model_fun as kin_mod


detector = apriltag.Detector()


def detect_all(frame):
    yshift, _, _ = frame.shape
    april_result = detect_apriltags(frame)
    # extract pose
    if len(april_result) > 0:
        alpha, eps = extract_alpha(april_result)
        X, Y, xref = extract_position(april_result)
        # coordinate transform:
        for idx, y in enumerate(Y):
            if y:
                Y[idx] = yshift - y
        if xref[1]:
            xref = (xref[0], yshift - xref[1])
    else:
        alpha, eps = [None]*6, None
        X, Y = [None]*6, [None]*6
        xref = (None, None)

    return alpha, eps, (X, Y), xref


#def calc_pose(alpha, eps, positions):
#    alpha_ = alpha[0:3] + alpha[4:6]
#    pose_coords, ell, bet = kin_mod.extract_pose(alpha_, eps, positions)
#    return pose_coords, ell, bet


def detect_apriltags(frame):
    # gray frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detect apriltags
    april_result = detector.detect(frame)
    return april_result


def extract_position(april_result):
    SHIFT = {
        0: [0, 1, 10],
        1: [0, 3, 26],
        2: [1, 0, 10],
        3: [0, 1, 10],
        4: [3, 0, -5],
        5: [1, 0, 10],
            }
    X, Y = [None]*6, [None]*6
    xref = (None, None)
    for res in april_result:
        tag_id = res.tag_id
        if tag_id == 6:
            xref = (int(res.center[0]), int(res.center[1]))
        elif tag_id in SHIFT:
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
        if (
         ori[POSs[tag_id][0]] is not None
         and ori[POSs[tag_id][1]] is not None):
            p0, p1 = (np.append(ori[POSs[tag_id][0]], 0),
                      np.append(ori[POSs[tag_id][1]], 0))

            angle[tag_id] = round(calc_angle(p0, p1, jump=jump), 1)

    # calc eps
    if len(center) == 2:
        p0, p1 = np.append(center[0], 0), np.append(center[1], 0)
        eps = np.mod(-round(calc_angle(p1-p0, [1, 0, 0]) + 180, 1), 360)

    return angle, eps


def draw_positions(img, position_coords, xref, yshift=None):
    X, Y = position_coords
    X = X + [xref[0]]
    Y = Y + [xref[1]]
    for tag_id, coords in enumerate(zip(X, Y)):
        x, y = coords
        if x is not None:
            if yshift:
                y = yshift - y
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


def calc_angle(vec1, vec2, rotate_angle=0., jump=np.pi*.5):
    theta = np.radians(rotate_angle)
    vec1 = rotate(vec1, theta)
    x1, y1, z1 = normalize(vec1)
    x2, y2, z2 = normalize(vec2)
    phi1 = np.arctan2(y1, x1)
    vec2 = rotate([x2, y2, 0], -phi1+jump)
    phi2 = np.degrees(np.arctan2(vec2[1], vec2[0]) - jump)

    return -phi2


def normalize(vec):
    x, y, z = vec
    l = np.sqrt(x**2 + y**2 + z**2)
    return x/l, y/l, z/l


def rotate(vec, theta):
    c, s = np.cos(theta), np.sin(theta)
    return (c*vec[0]-s*vec[1], s*vec[0]+c*vec[1], vec[2])


if __name__ == '__main__':
    import time
    from PIL import Image
    from PiVideoStream import PiVideoStream

    resolution = (1280, 960)
    vs = PiVideoStream(resolution=resolution).start()
    time.sleep(1.0)
    try:
        while True:
            frame = vs.read()
            alpha, eps, positions, xref = detect_all(frame)
            print('Alpha:\t', alpha)
            print('Epsilon:\t', eps)
            print('Positions:\t', positions)
            print('Xref:\t', xref)

            if alpha:
                img = draw_positions(frame, positions, xref, yshift=resolution[1])
            else:
                img = frame

            cv2.imshow("Frame", img)
            cv2.waitKey(1) & 0xFF

            # ssh-hack: add: 'DISPLAY=localhost:0.0' to your system-variables
            #img2 = Image.fromarray(img, 'RGB')
            #img2.show()

    finally:
        vs.stop()
