# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 15:58:28 2019

@author: AmP
"""


import numpy as np
from scipy.optimize import minimize




len_leg = 80
len_tor = 85

n_limbs = 5


def correct_measurement(alpha, eps, fpos, len_leg=len_leg, len_tor=len_tor):
    alpha = alpha[0:3] + alpha[4:]  # remove double torso measurement
    xpos, ypos = fpos[0], fpos[1]
    ell0 = [len_leg, len_leg, len_tor, len_leg, len_leg]
    # unknown
    
    X10 = [xpos[1], ypos[1]]
    beta0 = [0, 0, 0, 0, 0]
    eps0 = eps
    x0 = X10 + beta0 + [eps0]


    wx, walp, weps = 1, .01, .01

    def objective(x):
        X1, bet, eps = x[0:2], x[2:2+n_limbs], x[-1]
        angle = np.array(alpha) + np.array(bet)
        xpos_est, ypos_est = _calc_coords2(ell0, angle, eps, (X1))
        err = [np.linalg.norm([xpos[idx]-xpos_est[idx],
                               ypos[idx]-ypos_est[idx]]) for idx in range(6)]
        deps = eps - eps0
        obj = (wx*sum(err) + walp*np.linalg.norm(bet, 2) + weps*deps)

        return obj

    
    solution = minimize(objective, x0, method='COBYLA')  # , bounds=bnds)
    x = solution.x
    X1_opt, bet, eps_opt = x[0:2], x[2:2+n_limbs], x[-1]
    alpha_opt = np.array(alpha) + np.array(bet)
    alpha_opt = [round(a, 2) for a in alpha_opt]
    xpos_est, ypos_est = _calc_coords2(ell0, alpha_opt, eps_opt, X1_opt)
    # add additional bending angle
    alpha_opt = alpha_opt[0:3] + [-alpha_opt[2]] + alpha_opt[3:]
    eps_opt = round(eps_opt, 2)

    xpos_est = [int(xx) for xx in xpos_est]
    ypos_est = [int(yy) for yy in ypos_est]

    return (alpha_opt, eps_opt, (xpos_est, ypos_est))


def _calc_coords2(ell, alp, eps, X1):
    (xom, yom) = X1
    c1, c2, c3, c4 = _calc_phi(alp, eps)
    R = [_calc_rad(ell[i], alp[i]) for i in range(5)]

    # coords cp upper left leg
    xr1 = xom + np.cos(np.deg2rad(eps-alp[2]*.5))*R[0]
    yr1 = yom + np.sin(np.deg2rad(eps-alp[2]*.5))*R[0]
    # coords F1
    xf1 = xr1 - np.cos(np.deg2rad(c1))*R[0]
    yf1 = yr1 - np.sin(np.deg2rad(c1))*R[0]

    # coords cp R2
    xr2 = xom + np.cos(np.deg2rad(c1+alp[0]))*R[1]
    yr2 = yom + np.sin(np.deg2rad(c1+alp[0]))*R[1]
    # coords F2
    xf2 = xr2 + np.cos(np.deg2rad(180-c2))*R[1]
    yf2 = yr2 - np.sin(np.deg2rad(180-c2))*R[1]

    # coords cp torso
    xrom = xom + np.cos(np.deg2rad(90-c1-alp[0]))*R[2]
    yrom = yom - np.sin(np.deg2rad(90-c1-alp[0]))*R[2]
    # coords lower torso
    xum = xrom - np.cos(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[2]
    yum = yrom - np.sin(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[2]

    # coords cp R4
    xr4 = xum - np.cos(np.deg2rad(eps+alp[2]*.5))*R[4]
    yr4 = yum - np.sin(np.deg2rad(eps+alp[2]*.5))*R[4]
    # coords of F4
    xf4 = xr4 + np.cos(np.deg2rad(c4-180))*R[4]
    yf4 = yr4 + np.sin(np.deg2rad(c4-180))*R[4]

    # coords cp R3
    xr3 = xum + np.sin(np.deg2rad(eps+alp[2]*.5-90))*R[3]
    yr3 = yum - np.cos(np.deg2rad(eps+alp[2]*.5-90))*R[3]
    # coords of F3
    xf3 = xr3 - np.sin(np.deg2rad(eps+alp[2]*.5+alp[3]-90))*R[3]
    yf3 = yr3 + np.cos(np.deg2rad(eps+alp[2]*.5+alp[3]-90))*R[3]

    return [xf1, xom, xf2, xf3, xum, xf4], [yf1, yom, yf2, yf3, yum, yf4]


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


if __name__ == '__main__':
    import cv2
    import IMGprocessing

    fnames = ['test_inv_kin_01.jpg', 'test_inv_kin_02.jpg',
              'test_inv_kin_03.jpg', 'test_inv_kin_04.jpg']
    ell0 = [len_leg, len_leg, len_tor, len_leg, len_leg]

    for fname in fnames:
        frame = cv2.imread(fname, 1)

        # measure
        alpha, eps, positions, xref = IMGprocessing.detect_all(frame)
        IMGprocessing.draw_positions(frame, positions, xref, thick=1)
        X1 = (positions[0][1], positions[1][1])
        IMGprocessing.draw_eps(frame, X1, eps, color=(0, 128, 255))
        IMGprocessing.draw_pose(frame, alpha, eps, positions, ell0, col=(100,0,0))

        # correction
        alpha_opt, eps_opt, positions_opt = \
            correct_measurement(alpha, eps, positions)
        X1_opt = (positions_opt[0][1], positions_opt[1][1])
        IMGprocessing.draw_pose(frame, alpha_opt, eps_opt, positions_opt, ell0)
        IMGprocessing.draw_eps(frame, X1_opt, eps_opt, color=(255, 255, 255), dist=120)
        img = IMGprocessing.draw_positions(frame, positions_opt, xref,
                                           thick=2, col=(255, 255, 255))

        print('coords in main:')
        print('alp:\t', [round(opt-ori, 2) for ori, opt in zip(alpha, alpha_opt)])
        print('deps:\t', round(eps_opt - eps, 2))


        cv2.imshow('frame', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
