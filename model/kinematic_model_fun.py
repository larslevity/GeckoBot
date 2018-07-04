# -*- coding: utf-8 -*-
"""
Created on Tue July 18 10:31:13 2018

@author: AmP
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import matplotlib.animation as animation


f_len = 100.     # factor on length objective
f_ori = 0.001  # .0003     # factor on orientation objective
f_ang = 10     # factor on angle objective

blow = .9       # lower stretching bound
bup = 1.1       # upper stretching bound

dev_ang = 100  # allowed deviation of angles

arc_res = 40    # resolution of arcs

len_leg = 1
len_tor = 1.1

n_foot = 4
n_limbs = 5


def predict_pose(pattern, initial_pose, stats=False, debug=False):
    alpha, eps, F1 = initial_pose
    ell_nominal = (len_leg, len_leg, len_tor, len_leg, len_leg)
    xlast, rlast = _set_initial_pose(alpha, ell_nominal, eps, F1)

    data, data_fp, data_nfp, costs = [], [], [], []
    (x, y), (fpx, fpy), (nfpx, nfpy) = get_repr(xlast, rlast, (1, 0, 0, 0))
    data.append((x, y))
    data_fp.append((fpx, fpy))
    data_nfp.append((nfpx, nfpy))

    for idx, reference in enumerate(pattern):
        alpref_, f = reference
        alpref = []
        for jdx, alp in enumerate(alpref_):
            if jdx == 2:
                alpref.append(alp)
            else:
                alpref.append(alp if alp > 0 else 0.01)
        alplast, epslast = xlast[0:n_limbs], xlast[-1]
        philast = _calc_phi(alplast, epslast)

        # Initial guess
        x0 = xlast

        def objective(x):
            alp, ell, eps = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
            phi = _calc_phi(alp, eps)
            obj_ori, obj_len, obj_ang = 0, 0, 0
            for idx in range(n_foot):
                if f[idx]:
                    obj_ori = (obj_ori + (phi[idx] - philast[idx])**2)
            for idx in range(n_limbs):
                obj_ang = obj_ang + (alpref[idx]-alp[idx])**2
            for idx in range(n_limbs):
                obj_len = obj_len + (ell[idx]-ell_nominal[idx])**2
            objective = (f_ori*np.sqrt(obj_ori) + f_ang*np.sqrt(obj_ang) +
                         f_len*np.sqrt(obj_len))
            return objective

        def constraint1(x):
            """ feet should be at the right position """
            xf, yf = _calc_coords(x, rlast, f)
            xflast, yflast = rlast
            constraint = 0
            for idx in range(n_foot):
                if f[idx]:
                    constraint = constraint + \
                        np.sqrt((xflast[idx] - xf[idx])**2 +
                                (yflast[idx] - yf[idx])**2)
            return constraint

        bleg = (blow*len_leg, bup*len_leg)
        btor = (blow*len_tor, bup*len_tor)
        bang = [(alpref[i]-dev_ang, alpref[i]+dev_ang) for i in range(n_limbs)]
        bnds = (bang[0], bang[1], bang[2], bang[3], bang[4],
                bleg, bleg, btor, bleg, bleg,
                (-360, 360))
        con1 = {'type': 'eq', 'fun': constraint1}
        cons = ([con1])
        solution = minimize(objective, x0, method='SLSQP',
                            bounds=bnds, constraints=cons)
        x = solution.x
        alp, ell, eps = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
        phi = _calc_phi(alp, eps)
        r = _calc_coords(x, rlast, f)
        # save opt meta data
        xlast = x
        rlast = r
        if debug:
            print '\n\nPOSE ', idx, '\n'
            print 'constraint function: \t', round(constraint1(x), 2)
            print 'objective function: \t', round(objective(x), 2)
            print 'alpref: \t\t', [round(xx, 2) for xx in alpref]
            print 'alp: \t\t\t', [round(xx, 2) for xx in alp]
            print 'ell: \t\t\t', [round(xx, 2) for xx in ell], '\n'

            print 'rx: \t\t\t', [round(xx, 2) for xx in r[0]]
            print 'ry: \t\t\t', [round(xx, 2) for xx in r[1]]
            print 'phi: \t\t\t', [round(xx, 2) for xx in phi], '\n'

            print 'eps: \t\t\t', round(eps, 2)
        if stats:
            costs.append(objective(x))
            (xa, ya), (fpx, fpy), (nfpx, nfpy) = get_repr(x, r, f)
            data.append((xa, ya))
            data_fp.append((fpx, fpy))
            data_nfp.append((nfpx, nfpy))

    return x, r, (data, data_fp, data_nfp), costs


def _set_initial_pose(alpha, ell, eps, F1):
    alp = alpha
    x = flat_list([alp, ell, [eps]])
    f = [1, 0, 0, 0]
    rinit = ([F1[0], None, None, None], [F1[1], None, None, None])
    r = _calc_coords(x, rinit, f)
    return (x, r)


def _calc_coords(x, r, f):
    alp, ell, eps = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
    c1, c2, _, _ = _calc_phi(alp, eps)
    R = [_calc_rad(ell[i], alp[i]) for i in range(5)]

    if f[0]:
        xf1, yf1 = r[0][0], r[1][0]
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
    elif f[1]:
        xf2, yf2 = r[0][1], r[1][1]
        # coords cp upper right leg
        xr2 = xf2 - np.sin(np.deg2rad(c2-90))*R[1]
        yr2 = yf2 + np.cos(np.deg2rad(c2-90))*R[1]
        # coords upper torso
        xom = xr2 - np.sin(np.deg2rad(90-c2+alp[1]))*R[1]
        yom = yr2 - np.cos(np.deg2rad(90-c2+alp[1]))*R[1]
        # coords cp R1
        xr1 = xom + np.sin(np.deg2rad(90-c2+alp[1]))*R[0]
        yr1 = yom + np.cos(np.deg2rad(90-c2+alp[1]))*R[0]
        # coords F1
        xf1 = xr1 - np.sin(np.deg2rad(90-c2+alp[1]+alp[0]))*R[0]
        yf1 = yr1 - np.cos(np.deg2rad(90-c2+alp[1]+alp[0]))*R[0]
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

    return [xf1, xf2, xf3, xf4], [yf1, yf2, yf3, yf4]


def get_repr(x, r, f):
    alp, ell, eps = x[0:n_limbs], x[n_limbs:2*n_limbs], x[-1]
    c1, _, _, _ = _calc_phi(alp, eps)
    l1, l2, lg, l3, l4 = ell
    alp1, bet1, gam, alp2, bet2 = alp
    xf, yf = r

    x, y = [xf[0]], [yf[0]]
    # draw upper left leg
    xl1, yl1 = _calc_arc_coords((x[-1], y[-1]), c1, c1+alp1,
                                _calc_rad(l1, alp1))
    x = x + xl1
    y = y + yl1
    # draw torso
    xt, yt = _calc_arc_coords((x[-1], y[-1]), -90+c1+alp1, -90+c1+alp1+gam,
                              _calc_rad(lg, gam))
    x = x + xt
    y = y + yt
    # draw lower right leg
    xl4, yl4 = _calc_arc_coords((x[-1], y[-1]), -90+gam-(90-c1-alp1),
                                -90+gam-(90-c1-alp1)-bet2, _calc_rad(l4, bet2))
    x = x + xl4
    y = y + yl4
    # draw upper right leg
    xl2, yl2 = _calc_arc_coords((xl1[-1], yl1[-1]), c1+alp1,
                                c1+alp1+bet1, _calc_rad(l2, bet1))
    x = x + xl2
    y = y + yl2
    # draw lower left leg
    xl3, yl3 = _calc_arc_coords((xt[-1], yt[-1]), -90+gam-(90-c1-alp1),
                                -90+gam-(90-c1-alp1)+alp2, _calc_rad(l3, alp2))
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

    return (x, y), fp, nfp


def flat_list(l):
    return [item for sublist in l for item in sublist]


def _calc_len(radius, angle):
    return angle/360.*2*np.pi*radius


def _calc_rad(length, angle):
    return 360.*length/(2*np.pi*angle)


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


def calc_difference(phi0, phi1):
    theta = -np.radians(phi0)
    c, s = np.cos(theta), np.sin(theta)
    R = np.matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    x2 = np.cos(np.radians(phi1))
    y2 = np.sin(np.radians(phi1))
    vec_ = R*np.c_[[x2, y2, 0]]
    diff = np.degrees(np.arctan2(float(vec_[1]), float(vec_[0])))
    return diff


def _calc_phi(alpha, eps):
    c1 = np.mod(eps - alpha[0] - alpha[2]*.5 + 360, 360)
    c2 = np.mod(c1 + alpha[0] + alpha[1] + 360, 360)
    c3 = np.mod(180 + alpha[2] - alpha[1] + alpha[3] + c2 + 360, 360)
    c4 = np.mod(180 + alpha[2] + alpha[0] - alpha[4] + c1 + 360, 360)
    phi = [c1, c2, c3, c4]
    return phi


def fill_ptrn(opt_ptrn, res=5, n_cycles=1):
    n_poses = len(opt_ptrn)
    c, f = [], []
    for i in range(n_poses):
        ci, fi = opt_ptrn[i]
        c.append(ci)
        f.append(fi)

    filled_ptrn = []
    for i in range(n_poses):
        ip = i+1 if i+1 < n_poses else 0
        for r in range(res):
            w = r/(res-1.)
            pose = [round(c[i][p] + (c[ip][p]-c[i][p])*w, 2) for p in range(5)]
            filled_ptrn.append([pose, f[i]])
        filled_ptrn.append([c[ip], f[i]])

    ptrn_looped = [filled_ptrn for i in range(n_cycles)]
#    return ptrn_looped
    return flat_list(ptrn_looped)


def animate_gait(fig1, data, data_fp, data_nfp, inv=500):

    def update_line(num, data, line, data_fp, line_fp, data_nfp, line_nfp):
        x, y = data[num]
        fpx, fpy = data_fp[num]
        nfpx, nfpy = data_nfp[num]
        line.set_data(np.array([[x], [y]]))
        line_fp.set_data(np.array([[fpx], [fpy]]))
        line_nfp.set_data(np.array([[nfpx], [nfpy]]))
        return line, line_fp, line_nfp

    n = len(data)
    l, = plt.plot([], [], '.')
    lfp, = plt.plot([], [], 'o', markersize=15)
    lnfp, = plt.plot([], [], 'x', markersize=10)
    minx, maxx, miny, maxy = 0, 0, 0, 0
    for dataset in data:
        x, y = dataset
        minx = min(x) if minx > min(x) else minx
        maxx = max(x) if maxx < max(x) else maxx
        miny = min(y) if miny > min(y) else miny
        maxy = max(y) if maxy < max(y) else maxy
    plt.xlim(minx-1, maxx+1)
    plt.ylim(miny-1, maxy+1)
    line_ani = animation.FuncAnimation(
        fig1, update_line, n, fargs=(data, l, data_fp, lfp, data_nfp, lnfp),
        interval=inv, blit=True)
    return line_ani


def plot_gait(data, data_fp, data_nfp):
    plt.figure()
    plt.title('Plot')
    for idx in range(len(data)):
        (x, y) = data[idx]
        (fpx, fpy) = data_fp[idx]
        (nfpx, nfpy) = data_nfp[idx]
        c = (1-float(idx)/len(data))*.8
        col = (c, c, c)
        plt.plot(x, y, '.', color=col)
        plt.plot(fpx, fpy, 'o', markersize=10, color=col)
        plt.plot(nfpx, nfpy, 'x', markersize=10, color=col)
    plt.axis('equal')


def save_animation(line_ani, name='gait.mp4', conv='avconv'):
    # Set up formatting for the movie files
    Writer = animation.writers[conv]
    writer = Writer(fps=15, metadata=dict(artist='Lars Schiller'),
                    bitrate=1800)
    line_ani.save(name, writer=writer)


if __name__ == "__main__":
    """
    To save the animation you need the libav-tool to be installed:
    sudo apt-get install libav-tools
    """

    init_pose = [(.1, .1, .1, .1, .1), 90, (0, 2)]
    ref = [[[90, 0.01, 90, 90, 0.01], [1, 1, 1, 0]],
           [[90, 0.01, 90, 90, 0.01], [0, 1, 1, 0]],
           [[90, 0.01, 90, 90, 0.01], [0, 1, 0, 1]]
           ]

    x, r, data = predict_pose(ref, init_pose, True, True)
    plot_gait(*data)

    if 0:
        fig_ani = plt.figure()
        plt.title('Gecko-robot model animation')
        line_ani = animate_gait(fig_ani, *data)

    plt.show()
