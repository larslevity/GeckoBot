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
        alpha = extract_alpha(april_result)
        X, Y, xref = extract_position(april_result)
        eps = extract_eps(X, Y)
        # coordinate transform:
        for idx, y in enumerate(Y):
            if not np.isnan(y):
                Y[idx] = yshift - y
        if not np.isnan(xref[1]):
            xref = (xref[0], yshift - xref[1])
    else:
        alpha, eps = [np.nan]*6, np.nan
        X, Y = [np.nan]*6, [np.nan]*6
        xref = (np.nan, np.nan)

    return alpha, eps, (X, Y), xref


def detect_apriltags(frame):
    # gray frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detect apriltags
    april_result = detector.detect(frame)
    return april_result


def extract_position(april_result):
    SHIFT = {  # xshift, yshift
        0: [10, 5],
        1: [0, -15],
        2: [-10, 5],
        3: [10, -5],
        4: [0, -9],
        5: [-12, -5],
            }
    X, Y = [np.nan]*6, [np.nan]*6
    xref = (np.nan, np.nan)
    for res in april_result:
        tag_id = res.tag_id
        if tag_id == 6:
            xref = (int(res.center[0]), int(res.center[1]))
        elif tag_id in SHIFT:
            pc0 = np.array([res.corners[0][0], res.corners[0][1]])
            pc1 = np.array([res.corners[1][0], res.corners[1][1]])
            pc3 = np.array([res.corners[3][0], res.corners[3][1]])
            xshift = (pc1-pc0)/np.linalg.norm(pc1-pc0)*SHIFT[tag_id][0]
            yshift = (pc0-pc3)/np.linalg.norm(pc0-pc3)*SHIFT[tag_id][1]
            center = res.center + yshift + xshift
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
    for res in april_result:
        tag_id = res.tag_id
        if tag_id < 6:
            ori[tag_id] = res.corners[2] - res.corners[0]

    angle = [np.nan]*6
    for tag_id in POSs:
        if (
         ori[POSs[tag_id][0]] is not None
         and ori[POSs[tag_id][1]] is not None):
            p0, p1 = (np.append(ori[POSs[tag_id][0]], 0),
                      np.append(ori[POSs[tag_id][1]], 0))
            angle[tag_id] = round(calc_angle(p0, p1, jump=jump), 1)
    return angle


def extract_eps(X, Y):
    # calc eps
    eps = np.nan
    if not np.isnan(X[1]) and not np.isnan(X[4]):
        p0, p1 = np.array([X[1], Y[1], 0]), np.array([X[4], Y[4], 0])
        eps = np.mod(-round(calc_angle(p1-p0, [1, 0, 0]) + 180, 1), 360)
    return eps


def draw_positions(img, position_coords, xref, col=(255, 0, 0),
                   thick=2, size=2):
    yshift = img.shape[0]
    X, Y = position_coords
    X = X + [xref[0]]
    Y = Y + [xref[1]]
    for tag_id, coords in enumerate(zip(X, Y)):
        x, y = coords
        if not np.isnan(x):
            y = yshift - y
            cv2.rectangle(img, (x-size, y-size), (x+size, y+size), col, -1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontscale = .5
            cv2.putText(img, str(tag_id), (x, y-2*size),
                        font, fontscale, col, 2)
    # draw line
    if not np.isnan(X[1]) and not np.isnan(X[4]):
        cv2.line(img, (X[1], yshift-Y[1]), (X[4], yshift-Y[4]),
                 col, thick)
    if not np.isnan(X[1]) and not np.isnan(xref[0]):
        cv2.line(img, (X[1], yshift-Y[1]), (xref[0], yshift-xref[1]),
                 col, thick)

    return img


def draw_eps(img, X1, eps, color=(0, 0, 255), dist=100, thick=2):
     if not np.isnan(eps):   
        (h, w) = img.shape[:2]
        X2 = (int(X1[0] + np.cos(np.deg2rad(eps))*dist),
              h-int(X1[1] + np.sin(np.deg2rad(eps))*dist))
        cv2.line(img, (int(X1[0]), h-int(X1[1])), X2, color, thick)


def calc_angle(vec1, vec2, rotate_angle=0., jump=np.pi*.5):
    theta = np.radians(rotate_angle)
    vec1 = rotate(vec1, theta)
    x1, y1, z1 = normalize(vec1)
    x2, y2, z2 = normalize(vec2)
    phi1 = np.arctan2(y1, x1)
    vec2 = rotate([x2, y2, 0], -phi1+jump)
    phi2 = np.degrees(np.arctan2(vec2[1], vec2[0]) - jump)

    return -phi2


def draw_pose(img, alpha, eps, positions, ell, col=(255, 255, 255)):
    alpha = alpha[0:3] + alpha[4:]  # remove double torso measurement
    xpos, ypos = positions
    (xa, ya) = get_repr(alpha, ell, eps, [xpos[0], ypos[0]])
    yshift = img.shape[0]
    for x, y in zip(xa, ya):
        cv2.circle(img, (int(x), int(yshift-y)), 1, col)


arc_res = 20    # resolution of arcs

def _calc_arc_coords(xy, alp1, alp2, rad):
    x0, y0 = xy
    x, y = [x0], [y0]
    xr = x0 + np.cos(np.deg2rad(alp1))*rad
    yr = y0 + np.sin(np.deg2rad(alp1))*rad
    steps = [angle for angle in np.linspace(0, alp2-alp1, arc_res)]
    for dangle in steps:
        x.append(xr - np.sin(np.deg2rad(90-alp1-dangle))*rad)
        y.append(yr - np.cos(np.deg2rad(90-alp1-dangle))*rad)
    return x, y


def _calc_rad(length, angle):
    if abs(angle) < 0.1:
        angle = .1
    return 360.*length/(2*np.pi*angle)


def _calc_phi(alpha, eps):
    c1 = np.mod(eps - alpha[0] - alpha[2]*.5 + 360, 360)
    c2 = np.mod(eps + alpha[1] - alpha[2]*.5 + 360, 360)
    c3 = np.mod(180 + eps + alpha[3] + alpha[2]*.5 + 360, 360)
    c4 = np.mod(180 + eps - alpha[4] + alpha[2]*.5 + 360, 360)
    phi = [c1, c2, c3, c4]
    return phi


def get_repr(alp, ell, eps, f1pos):
    c1, c2, c3, c4 = _calc_phi(alp, eps)
    xf1, yf1 = f1pos
#    print('\ncoords inside get_repr:')
#    print('ell\t:', [round(l, 2) for l in ell])
#    print('alp\t:', [round(a, 2) for a in alp])
#    print('\n')

    x, y = [xf1], [yf1]
    # draw upper left leg
    xl1, yl1 = _calc_arc_coords((x[-1], y[-1]), c1, c1+alp[0],
                                _calc_rad(ell[0], alp[0]))
    x = x + xl1
    y = y + yl1

    # draw torso
    xt, yt = _calc_arc_coords((x[-1], y[-1]), -90+c1+alp[0], -90+c1+alp[0]+alp[2],
                              _calc_rad(ell[2], alp[2]))
    x = x + xt
    y = y + yt

    # draw lower right leg
    xl4, yl4 = _calc_arc_coords((x[-1], y[-1]), c4+alp[4],
                                c4, _calc_rad(ell[4], alp[4]))
    x = x + xl4
    y = y + yl4

    # draw upper right leg
    xl2, yl2 = _calc_arc_coords((xl1[-1], yl1[-1]), c2-alp[1],
                                c2, _calc_rad(ell[1], alp[1]))
    x = x + xl2
    y = y + yl2

    # draw lower left leg
    xl3, yl3 = _calc_arc_coords((xt[-1], yt[-1]), c3-alp[3],
                                c3, _calc_rad(ell[3], alp[3]))
    x = x + xl3
    y = y + yl3

    return (x, y)


def normalize(vec):
    x, y, z = vec
    l = np.sqrt(x**2 + y**2 + z**2)
    return x/l, y/l, z/l


def rotate(vec, theta):
    c, s = np.cos(theta), np.sin(theta)
    return (c*vec[0]-s*vec[1], s*vec[0]+c*vec[1], vec[2])


if __name__ == '__main__':
    import time
    from PiVideoStream import PiVideoStream
    import imutils
    import inverse_kinematics as inv_kin

    import sys
    from os import path
    sys.path.append(path.dirname(path.dirname(path.dirname(
            path.abspath(__file__)))))

    from Controller import calibration



    version = 'v40'
    # resolution = (1280, 720)
    # resolution = (1920, 1080)
#    resolution = (1648, 928)
    resolution = (1648, 1232)  # Halle
    
    len_leg, len_tor = calibration.get_len(version)
    
    ell0 = [len_leg, len_leg, len_tor, len_leg, len_leg]
    count_tag_fail = [0]*6

    vs = PiVideoStream(resolution=resolution).start()
    time.sleep(1.0)
    try:
        while True:
            frame = vs.read()
            alpha, eps, positions, xref = detect_all(frame)
            draw_positions(frame, positions, xref, thick=1)
            X1 = (positions[0][1], positions[1][1])
            draw_eps(frame, X1, eps, color=(0, 128, 255))

            fails = list(filter(lambda x: np.isnan(positions[0][x]), range(6)))
            for idx in fails:
                count_tag_fail[idx] += 1
            print('fail count:', count_tag_fail)

#            if not np.isnan(alpha).any():
#                (alpha_opt, eps_opt, positions_opt) = \
#                    inv_kin.correct_measurement(alpha, eps, positions, len_leg,
#                                                len_tor)
#                X1_opt = (positions_opt[0][1], positions_opt[1][1])
#                draw_pose(frame, alpha_opt, eps_opt, positions_opt, ell0)
#                draw_eps(frame, X1_opt, eps_opt, color=(255, 255, 0), dist=120)
#                    
#            else:
#                fails = list(filter(lambda x: np.isnan(positions[0][x]), range(6)))
#                for idx in fails:
#                    count_tag_fail[idx] += 1
#                print('fail count:', count_tag_fail)
#                alpha, eps = [np.nan]*6, np.nan
#                positions = ([np.nan]*6, [np.nan]*6)
#                xref = (np.nan, np.nan)

#            print('Alpha:\t', alpha)
#            print('Epsilon:\t', eps)
#            print('Positions:\t', positions)
#            print('Xref:\t', xref)


            # rotate
            scale = .5
            img = imutils.rotate_bound(frame, 270)
            img = cv2.resize(img, (0, 0), fx=scale, fy=scale)

            cv2.imshow("Frame", img)
            cv2.waitKey(1) & 0xFF

            # ssh-hack: add: 'DISPLAY=localhost:0.0' to your system-variables
            #img2 = Image.fromarray(img, 'RGB')
            #img2.show()

    finally:
        vs.stop()
