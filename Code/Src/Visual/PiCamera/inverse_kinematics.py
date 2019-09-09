# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 15:58:28 2019

@author: AmP
"""


import numpy as np
from scipy.optimize import minimize


arc_res = 20    # resolution of arcs

len_leg = 75
len_tor = 80

n_foot = 4
n_limbs = 5


def extract_pose(alpha, eps, fpos, len_leg=len_leg, len_tor=len_tor):
    # unknown
    ell0 = [len_leg, len_leg, len_tor, len_leg, len_leg]
    beta0 = [0, 0, 0, 0]
    x0 = ell0 + beta0
    xpos, ypos = fpos[0], fpos[1]

    w1, w2 = 1, 1

    def objective(x):
        _, bet = x[0:n_limbs], x[n_limbs:]
        xpos_est, ypos_est = _calc_coords2(x, alpha, eps, (xpos[0], ypos[0]))
        err = [np.linalg.norm([xpos[idx]-xpos_est[idx],
                               ypos[idx]-ypos_est[idx]]) for idx in range(6)]
        obj = w1*sum(err) + w2*np.linalg.norm(bet, 2)

        return obj

#    bleg = (blow*len_leg, bup*len_leg)
#    btor = (blow*len_tor, bup*len_tor)
#    bbet = [(-20, 20)]*4
#    bnds = (bbet[0], bbet[1], bbet[2], bbet[3], bleg, bleg, btor, bleg, bleg)

    solution = minimize(objective, x0, method='COBYLA')  # , bounds=bnds)
    x = solution.x
    ell, bet = x[0:n_limbs], x[n_limbs:]
    xpos_est, ypos_est = _calc_coords2(x, alpha, eps, (xpos[0], ypos[0]))

    r = ([xpos[0]]+xpos[2:4]+[xpos[5]],
         [ypos[0]]+ypos[2:4]+[ypos[5]])

    x_ = list(alpha) + list(ell) + [eps]
    (xa, ya), ((fpx, fpy), (nfpx, nfpy)) = get_repr(x_, r, [1, 1, 1, 1])

    return ((xa, ya), ell, bet)


def _calc_coords2(x, alp, eps, xfeet):
    (xf1, yf1) = xfeet
    ell, _ = x[0:n_limbs], x[n_limbs:]
    c1, c2, _, _ = _calc_phi(alp, eps)
    R = [_calc_rad(ell[i], alp[i]) for i in range(5)]

    # coords cp upper left leg
    xr1 = xf1 + np.cos(np.deg2rad(c1))*R[0]
    yr1 = yf1 - np.sin(np.deg2rad(c1))*R[0]
    # coords upper torso
    xom = xr1 - np.sin(np.deg2rad(90-c1-alp[0]))*R[0]
    yom = yr1 + np.cos(np.deg2rad(90-c1-alp[0]))*R[0]
    # coords cp R2
    xr2 = xom + np.cos(np.deg2rad(c1+alp[0]))*R[1]
    yr2 = yom - np.sin(np.deg2rad(c1+alp[0]))*R[1]
    # coords F2
    xf2 = xr2 + np.sin(np.deg2rad(alp[1] - (90-c1-alp[0])))*R[1]
    yf2 = yr2 + np.cos(np.deg2rad(alp[1] - (90-c1-alp[0])))*R[1]

    # coords cp torso
    xrom = xom + np.cos(np.deg2rad(90-c1-alp[0]))*R[2]
    yrom = yom + np.sin(np.deg2rad(90-c1-alp[0]))*R[2]
    # coords lower torso
    xum = xrom - np.cos(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[2]
    yum = yrom + np.sin(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[2]
    # coords cp lower right foot
    xr4 = xum + np.sin(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[4]
    yr4 = yum + np.cos(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[4]
    # coords of F4
    xf4 = xr4 + np.sin(np.deg2rad(alp[4] - (alp[2] - (90-c1-alp[0]))))*R[4]
    yf4 = yr4 - np.cos(np.deg2rad(alp[4] - (alp[2] - (90-c1-alp[0]))))*R[4]
    # coords cp R3
    xr3 = xum + np.sin(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[3]
    yr3 = yum + np.cos(np.deg2rad(alp[2] - (90-c1-alp[0])))*R[3]
    # coords of F3
    xf3 = xr3 - np.cos(np.deg2rad(-alp[3] - alp[2] + 180-c1-alp[0]))*R[3]
    yf3 = yr3 - np.sin(np.deg2rad(-alp[3] - alp[2] + 180-c1-alp[0]))*R[3]

    return [xf1, xom, xf2, xf3, xum, xf4], [yf1, yom, yf2, yf3, yum, yf4]


def get_repr(x, r, f):
    alp, ell, eps = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
    c1, _, _, _ = _calc_phi(alp, eps)
    l1, l2, lg, l3, l4 = ell
    alp1, bet1, gam, alp2, bet2 = alp
    xf, yf = r

    x, y = [xf[0]], [yf[0]]
    # draw upper left leg
    xl1, yl1 = _calc_arc_coords((x[-1], y[-1]), c1, c1+alp1,
                                _calc_rad(l1, alp1), imgcoords=True)
    x = x + xl1
    y = y + yl1
    # draw torso
    xt, yt = _calc_arc_coords((x[-1], y[-1]), -90+c1+alp1, -90+c1+alp1+gam,
                              _calc_rad(lg, gam))
    x = x + xt
    y = y + yt
    # draw lower right leg
    xl4, yl4 = _calc_arc_coords((x[-1], y[-1]), -90+gam-(90-c1-alp1),
                                -90+gam-(90-c1-alp1)-bet2, _calc_rad(l4, bet2),
                                imgcoords=True)
    x = x + xl4
    y = y + yl4
    # draw upper right leg
    xl2, yl2 = _calc_arc_coords((xl1[-1], yl1[-1]), c1+alp1,
                                c1+alp1+bet1, _calc_rad(l2, bet1),
                                imgcoords=True)
    x = x + xl2
    y = y + yl2
    # draw lower left leg
    xl3, yl3 = _calc_arc_coords((xt[-1], yt[-1]), -90+gam-(90-c1-alp1),
                                -90+gam-(90-c1-alp1)+alp2, _calc_rad(l3, alp2),
                                imgcoords=True)
    x = x + xl3
    y = y + yl3

    fp = ([], [])
    nfp = ([], [])
    for idx in range(n_foot):
        if f[idx]:
            fp[0].append(xf[idx])
            fp[1].append(yf[idx])
        else:
            nfp[0].append(xf[idx])
            nfp[1].append(yf[idx])

    return (x, y), (fp, nfp)


def _calc_rad(length, angle):
    if abs(angle) < 0.1:
        angle=.1
        
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
    c2 = np.mod(c1 + alpha[0] + alpha[1] + 360, 360)
    c3 = np.mod(180 + alpha[2] - alpha[1] + alpha[3] + c2 + 360, 360)
    c4 = np.mod(180 + alpha[2] + alpha[0] - alpha[4] + c1 + 360, 360)
    phi = [c1, c2, c3, c4]
    return phi
