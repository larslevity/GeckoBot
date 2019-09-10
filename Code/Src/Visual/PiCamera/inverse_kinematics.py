# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 15:58:28 2019

@author: AmP
"""


import numpy as np
from scipy.optimize import minimize


arc_res = 20    # resolution of arcs

len_leg = 65
len_tor = 70

n_foot = 4
n_limbs = 5


def extract_pose(alpha, eps, fpos, len_leg=len_leg, len_tor=len_tor):
    alpha = alpha[0:3] + alpha[4:]  # remove double torso measurement
    # unknown
    ell0 = [len_leg, len_leg, len_tor, len_leg, len_leg]
    beta0 = [0, 0, 0, 0, 0]
    eps0 = eps
    x0 = ell0 + beta0 + [eps0]
    xpos, ypos = fpos[0], fpos[1]

    w1, w2, w3, weps = 1, .01, .1, .01

    def objective(x):
        ell, bet, eps = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
        angle = np.array(alpha) + np.array(bet)
        xpos_est, ypos_est = _calc_coords2(x, angle, eps, (xpos[0], ypos[0]))
        err = [np.linalg.norm([xpos[idx]-xpos_est[idx],
                               ypos[idx]-ypos_est[idx]]) for idx in range(6)]
        dell = np.array(ell) - np.array(ell0)
        deps = eps - eps0
        obj = (w1*sum(err) + w2*np.linalg.norm(bet, 2)
               + w3*np.linalg.norm(dell) + weps*deps)

        return obj

    solution = minimize(objective, x0, method='COBYLA')  # , bounds=bnds)
    x = solution.x
    ell, bet, eps_opt = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
    alpha_opt = np.array(alpha) + np.array(bet)

    xpos_est, ypos_est = _calc_coords2(x, alpha_opt, eps_opt,
                                       (xpos[0], ypos[0]))

    x_ = list(alpha_opt) + list(ell) + [eps_opt]
    (xa, ya) = get_repr(x_, [xpos_est[0], ypos_est[0]])

    return ((xa, ya), ell, bet, eps_opt)


def _calc_coords2(x, alp, eps, xfeet):
    (xf1, yf1) = xfeet
    ell, _ = x[0:n_limbs], x[n_limbs:]
    c1, c2, _, _ = _calc_phi(alp, eps)
    R = [_calc_rad(ell[i], alp[i]) for i in range(5)]

    # coords cp upper left leg
    xr1 = xf1 + np.cos(np.deg2rad(c1))*R[0]
    yr1 = yf1 + np.sin(np.deg2rad(c1))*R[0]
    # coords upper torso
    xom = xr1 - np.sin(np.deg2rad(90-c1-alp[0]))*R[0]
    yom = yr1 - np.cos(np.deg2rad(90-c1-alp[0]))*R[0]
    # coords cp R2
    xr2 = xom + np.cos(np.deg2rad(c1+alp[0]))*R[1]
    yr2 = yom + np.sin(np.deg2rad(c1+alp[0]))*R[1]
    # coords F2
    xf2 = xr2 + np.sin(np.deg2rad(alp[1] - (90-c1-alp[0])))*R[1]
    yf2 = yr2 - np.cos(np.deg2rad(alp[1] - (90-c1-alp[0])))*R[1]

    # coords cp torso
    xrom = xom + np.cos(np.deg2rad(90-c1-alp[0]))*R[2]
    yrom = yom - np.sin(np.deg2rad(90-c1-alp[0]))*R[2]
    # coords lower torso
    xum = xrom - np.cos(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[2]
    yum = yrom - np.sin(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[2]
    # coords cp lower right foot
    xr4 = xum + np.sin(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[4]
    yr4 = yum - np.cos(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[4]
    # coords of F4
    xf4 = xr4 + np.sin(np.deg2rad(alp[4] - (alp[2] - (90-c1-alp[0]))))*R[4]
    yf4 = yr4 + np.cos(np.deg2rad(alp[4] - (alp[2] - (90-c1-alp[0]))))*R[4]
    # coords cp R3
    xr3 = xum + np.sin(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[3]
    yr3 = yum - np.cos(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[3]
    # coords of F3
    xf3 = xr3 - np.cos(np.deg2rad(-alp[3] - alp[2] + 180-c1-alp[0]))*R[3]
    yf3 = yr3 + np.sin(np.deg2rad(-alp[3] - alp[2] + 180-c1-alp[0]))*R[3]

    return [xf1, xom, xf2, xf3, xum, xf4], [yf1, yom, yf2, yf3, yum, yf4]


def get_repr(x, f1pos):
    alp, ell, eps = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
    c1, c2, c3, c4 = _calc_phi(alp, eps)
    xf1, yf1 = f1pos
    print('\ncoords inside get_repr:')
    print('ell\t:', [round(l, 2) for l in ell])
    print('alp\t:', [round(a, 2) for a in alp])
    print('\n')

    x, y = [xf1], [yf1]
    # draw upper left leg
    xl1, yl1 = _calc_arc_coords((x[-1], y[-1]), c1, c1+alp[0],
                                _calc_rad(ell[0], alp[0]), imgcoords=False)
    x = x + xl1
    y = y + yl1

    # draw torso
    xt, yt = _calc_arc_coords((x[-1], y[-1]), -90+c1+alp[0], -90+c1+alp[0]+alp[2],
                              _calc_rad(ell[2], alp[2]))
    x = x + xt
    y = y + yt

    # draw lower right leg
    xl4, yl4 = _calc_arc_coords((x[-1], y[-1]), c4+alp[4],
                                c4, _calc_rad(ell[4], alp[4]),
                                imgcoords=False)
    x = x + xl4
    y = y + yl4

    # draw upper right leg
    xl2, yl2 = _calc_arc_coords((xl1[-1], yl1[-1]), c2-alp[1],
                                c2, _calc_rad(ell[1], alp[1]),
                                imgcoords=False)
    x = x + xl2
    y = y + yl2

    # draw lower left leg
    xl3, yl3 = _calc_arc_coords((xt[-1], yt[-1]), c3-alp[3],
                                c3, _calc_rad(ell[3], alp[3]),
                                imgcoords=False)
    x = x + xl3
    y = y + yl3

    return (x, y)


def _calc_rad(length, angle):
    if abs(angle) < 0.1:
        angle = .1
    return 360.*length/(2*np.pi*angle)


def _calc_arc_coords(xy, alp1, alp2, rad, imgcoords=False):
    x0, y0 = xy
    x, y = [x0], [y0]
    xr = x0 + np.cos(np.deg2rad(alp1))*rad
    if imgcoords:
        yr = y0 - np.sin(np.deg2rad(alp1))*rad
    else:
        yr = y0 + np.sin(np.deg2rad(alp1))*rad
    steps = [angle for angle in np.linspace(0, alp2-alp1, arc_res)]
    for dangle in steps:
        x.append(xr - np.sin(np.deg2rad(90-alp1-dangle))*rad)
        if imgcoords:
            y.append(yr + np.cos(np.deg2rad(90-alp1-dangle))*rad)
        else:
            y.append(yr - np.cos(np.deg2rad(90-alp1-dangle))*rad)

    return x, y


def _calc_phi(alpha, eps):
    c1 = np.mod(eps - alpha[0] - alpha[2]*.5 + 360, 360)
    c2 = np.mod(eps + alpha[1] - alpha[2]*.5 + 360, 360)
    c3 = np.mod(180 + eps + alpha[3] + alpha[2]*.5 + 360, 360)
    c4 = np.mod(180 + eps - alpha[4] + alpha[2]*.5 + 360, 360)
    phi = [c1, c2, c3, c4]
    return phi


if __name__ == '__main__':
    import cv2
    import IMGprocessing

    frame = cv2.imread('test_inv_kin.jpg', 1)
    resolution = (1648, 928)
    (h, w) = frame.shape[:2]
    scale = resolution[1] / float(h)
    frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    (h, w) = frame.shape[:2]
    resolution = (w, h)

    alpha, eps, positions, xref = IMGprocessing.detect_all(frame)
    yshift = resolution[1]
    IMGprocessing.draw_positions(frame, positions, xref, yshift=yshift)
    X1 = (positions[0][1], positions[1][1])
    IMGprocessing.draw_eps(frame, X1, eps)

    (xa, ya), ell, bet, eps_opt = extract_pose(alpha, eps, positions)
    print('coords in main:')
    print('ell:\t', [round(l, 2) for l in ell])
    print('alp:\t', [round(a, 2) for a in alpha])
    print('deps:\t', round(eps_opt - eps, 2))

    for x, y in zip(xa, ya):
        cv2.circle(frame, (int(x), int(yshift-y)), 1, (255, 255, 255))
    IMGprocessing.draw_eps(frame, X1, eps_opt, color=(0, 0, 0), dist=50)

    cv2.imshow('frame', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
