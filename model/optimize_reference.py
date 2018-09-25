# -*- coding: utf-8 -*-
"""
Created on Tue Jul 03 14:33:49 2018

@author: Lars Schiller (AmP)
"""
import kinematic_model_fun as model
from scipy.optimize import minimize
from scipy.optimize import basinhopping
import numpy as np


def gnerate_ptrn_symmetric(X, n_cycles):
    ptrn = []
    for n in range(n_cycles):
        p = X
        ptrn.append([[p[0], p[1], p[2], p[3], p[4]], [1, 0, 0, 1]])
        ptrn.append([[p[1], p[0], -p[2], p[4], p[3]], [0, 1, 1, 0]])
    return ptrn


def gnerate_ptrn(X, n_cycles):
    ptrn = []
    for n in range(n_cycles):
        p = X
        ptrn.append([[p[0], p[1], p[2], p[3], p[4]], [1, 0, 0, 1]])
        ptrn.append([[p[5], p[6], p[7], p[8], p[9]], [0, 1, 1, 0]])
    return ptrn


def gnerate_ptrn_3fixed_1(X, n_cycles):
    ptrn = []
    for n in range(n_cycles):
        p = X
        ptrn.append([[p[0], p[1], p[2], p[3], p[4]], [1, 0, 1, 1]])
        ptrn.append([[p[5], p[6], p[7], p[8], p[9]], [0, 1, 1, 1]])
        ptrn.append([[p[10], p[11], p[12], p[13], p[14]], [1, 1, 0, 1]])
        ptrn.append([[p[15], p[16], p[17], p[18], p[19]], [1, 1, 1, 0]])
    return ptrn


def gnerate_ptrn_3fixed_2(X, n_cycles):
    ptrn = []
    for n in range(n_cycles):
        p = X
        ptrn.append([[p[0], p[1], p[2], p[3], p[4]], [1, 1, 0, 1]])
        ptrn.append([[p[5], p[6], p[7], p[8], p[9]], [0, 1, 1, 1]])
        ptrn.append([[p[10], p[11], p[12], p[13], p[14]], [1, 0, 1, 1]])
        ptrn.append([[p[15], p[16], p[17], p[18], p[19]], [1, 1, 1, 0]])
    return ptrn


def gnerate_ptrn_3fixed_3(X, n_cycles):
    ptrn = []
    for n in range(n_cycles):
        p = X
        ptrn.append([[p[0], p[1], p[2], p[3], p[4]], [1, 1, 1, 0]])
        ptrn.append([[p[5], p[6], p[7], p[8], p[9]], [0, 1, 1, 1]])
        ptrn.append([[p[10], p[11], p[12], p[13], p[14]], [1, 0, 1, 1]])
        ptrn.append([[p[15], p[16], p[17], p[18], p[19]], [1, 1, 0, 1]])
    return ptrn


def optimize_gait_3fixed(n_cycles, initial_pose, method='COBYLA',
                         x0=[90, .1, -90, 90, .1], f=None):
    obj_history = []
    bleg = (0.1, 120)
    btor = (-120, 120)
    bnds = [bleg, bleg, btor, bleg, bleg]*4
    X0 = x0*4

    def objective_3fixed(X):
        ptrn = gnerate_ptrn_3fixed_1(X, n_cycles)
        if f:
            xfinal, rfinal, _, _ = model.predict_pose(ptrn, initial_pose, f=f)
        else:
            xfinal, rfinal, _, _ = model.predict_pose(ptrn, initial_pose)
        xfp, yfp = rfinal
        obj = -np.sqrt((sum(yfp))**2 + (sum(xfp))**2)
        obj_history.append(obj)
        print 'step', len(obj_history), '\t', obj
        return obj

    solution = minimize(objective_3fixed, X0, method=method, bounds=bnds)
    X = solution.x
    ptrn = gnerate_ptrn_3fixed_1(X, n_cycles)
    return ptrn, obj_history, objective_3fixed(X)


def optimize_gait_straight(n_cycles, method='COBYLA',
                           x0=[90, .1, -90, 90, .1], f=None):
    obj_history = []
    bleg = (0.1, 120)
    btor = (-120, 120)
    bnds = [bleg, bleg, btor, bleg, bleg]
    X0 = x0

    def objective_straight(X):
        initial_pose = [X, 90, (0, 0)]
        ptrn = gnerate_ptrn_symmetric(X, n_cycles)
        if f:
            xfinal, rfinal, data_sim, _ = model.predict_pose(ptrn,
                                                             initial_pose,
                                                             stats=1, f=f)
        else:
            xfinal, rfinal, data_sim, _ = model.predict_pose(ptrn,
                                                             initial_pose)
        _, data_fp, data_nfp, _ = data_sim
        _, yfp0 = data_fp[0]
        _, ynfp0 = data_nfp[0]
        xfp, yfp = rfinal
        obj = -(sum(yfp)-sum(yfp0+ynfp0))
        obj_history.append(obj)
        print 'step', len(obj_history), '\t', obj
        # , '\n', yfp, '\n', yfp0+ynfp0, '\n\n'
        return obj

    solution = minimize(objective_straight, X0, method=method, bounds=bnds)
    X = solution.x
    ptrn = gnerate_ptrn_symmetric(X, n_cycles)
    return ptrn, obj_history, objective_straight(X)


def optimize_gait_curve(n_cycles, method='COBYLA',
                        x0=[90, .1, -90, 90, .1], f=None):
    obj_history = []
    bleg = (0.01, 120)
    btor = (-120, 120)
    bnds = [bleg, bleg, btor, bleg, bleg, bleg, bleg, btor, bleg, bleg]
    X0 = model.flat_list([x0, x0])

    def objective_curve(X):
        initial_pose = [X[:5], 90, (0, 0)]
        ptrn = gnerate_ptrn(X, n_cycles)
        xfinal, rfinal, _, _ = model.predict_pose(ptrn, initial_pose, f=f)
        eps = xfinal[-1]
        obj = -eps
        obj_history.append(obj)
        print 'step', len(obj_history), '\t', obj
        return obj

    solution = minimize(objective_curve, X0, method=method, bounds=bnds)
    X = solution.x
    ptrn = gnerate_ptrn(X, n_cycles)
    return ptrn, obj_history, objective_curve(X)


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    """
    for the initial pose:
        init_pose = [[.1, 90, 90, .1, 90], 90, (0, 3)]
        n_cycles = 1
        X0 = [90, .1, -90, 90, .1,
              .1, 90, 90, .1, 90]
    the following stats are recorded:

    method | nfev | obj
    -------|------|-------
    COBYLA | 200  | 10.9
    TNC    | 480  | 12.85 (na)
    CG     | 324  | 12.85 (na)
    Powell | 1891 | 16.09

    _______________________________________________________________

    for the initial pose:
        init_pose = [[.1, 90, 90, .1, 90], 90, (0, 3)]
        n_cycles = 1
        X0 = [50, .1, -50, 50, .1,
              .1, 50, 50, .1, 50]
    the following stats are recorded:

    method | nfev | obj
    -------|------|-------
    COBYLA | 257  | 16.85
    TNC    | 157  | 11.09 (na)
    CG     | 1093 | 11.09 (na)
    Powell | 1587 | 14.09
    """

    f_len = 100.     # factor on length objective
    f_ori = .0001  # .0003     # factor on orientation objective
    f_ang = 10     # factor on angle objective
    f = [f_len, f_ori, f_ang]
    methods = ['Powell', 'COBYLA', 'CG', 'TNC', 'SLSQP']
    x0 = [90, .1, -90, 90, .1]
    method = methods[1]
    n_cycles = 2
#    opt_ptrn, obj_hist, opt_obj = optimize_gait_straight(n_cycles,
#                                                         method, x0=x0, f=f)
    opt_ptrn, obj_hist, opt_obj = optimize_gait_curve(n_cycles, method=method,
                                                      x0=x0, f=f)
    opt_ptrn = opt_ptrn[:2]
    init_pose = [opt_ptrn[0][0], 90, (0, 0)]

#    opt_ptrn, obj_hist, opt_obj = optimize_gait_3fixed(n_cycles, init_pose,
#                                                       method, x0=x0)
#    opt_ptrn = opt_ptrn[:4]

    filled_ptrn = model.fill_ptrn(opt_ptrn, n_cycles=2, res=2)
    prop_str = '{} | {} | {} | {} | {}'.format(
            method, len(obj_hist), round(opt_obj, 2), n_cycles, f_ori)

    x, r, data, cst = model.predict_pose(filled_ptrn, init_pose, stats=1, f=f)
    model.plot_gait(*data, name='Plot: ' + prop_str)

    plt.figure('cost: ' + prop_str)
    plt.title('cost: ' + prop_str)
    plt.plot(cst)

    plt.figure('opt_hist: ' + prop_str)
    plt.title('opt_hist: ' + prop_str)
    plt.plot(obj_hist)

    print x0
    print prop_str
    print '\n', opt_ptrn, '\n'

    fig = plt.figure('Animation: ' + prop_str)
    plt.title('Animation: ' + prop_str)
    lin = model.animate_gait(fig, *data)
    plt.show()


# _______________________________________________________________
#    Straight tries
#    opt_ptrn = [[[60, 12, -100, 60, 12], [1, 0, 0, 1]],  # slightly modified
#                [[12, 60, 100, 12, 60], [0, 1, 1, 0]]]

#    opt_ptrn = [[[39, 22, -110, 25, 13], [1, 0, 0, 1]],  # opt sym sol
#                [[22, 39, 110, 13, 25], [0, 1, 1, 0]]]

# _______________________________________________________________
#    Straight opt pattrns:
#    opt_ptrn = [[[35, 12, -97, 40, 12], [1, 0, 0, 1]],  # 1 cycle
#                [[12, 35, 97, 12, 40], [0, 1, 1, 0]]]

#    opt_ptrn = [[[35, 12, -97, 41, 15], [1, 0, 0, 1]],  # 2 cycle
#                [[12, 35, 97, 15, 41], [0, 1, 1, 0]]]

#    opt_ptrn = [[[34, 10, -98, 41, 14], [1, 0, 0, 1]],  # 3 cycle **
#                [[10, 34, 98, 14, 41], [0, 1, 1, 0]]]

#    opt_ptrn = [[[0.1, 18, -85, 0.1, 22], [1, 0, 0, 1]],  # 3 cycle ***
#                [[18, 0.1, 85, 22, 0.1], [0, 1, 1, 0]]]

# _______________________________________________________________
#    Straight opt pattrns (different f_ori weights):
#    opt_ptrn = [[[.01, 25, -85, .01, 21], [0, 1, 1, 0]],  # 3 cycle f_ori=.1
#                [[25, .01, 85, 21, .01], [1, 0, 0, 1]]]

#    opt_ptrn = [[[86, 4, -110, 83, 4], [0, 1, 1, 0]],  # 5 cycle f_ori=.01
#                [[4, 86, 110, 4, 83], [1, 0, 0, 1]]]

#    opt_ptrn = [[[90, 1, -90, 91, .01], [0, 1, 1, 0]],  # 5 cycle f_ori=10
#                [[1, 90, 110, .01, 91], [1, 0, 0, 1]]]


# _______________________________________________________________
#    Curve opt pattrns
#    opt_ptrn = [[[16, -57, -35, -7, -40], [1, 0, 0, 1]],  # 1 cycle
#                [[52, 74, -60, 100, 5], [0, 1, 1, 0]]]

#    opt_ptrn = [[[16, -60, -37, -3, -37], [1, 0, 0, 1]],  # 2 cycle
#                [[77, 66, -93, 90, 30], [0, 1, 1, 0]]]

#    opt_ptrn = [[[-13, -87, -45, -30, -72], [1, 0, 0, 1]],  # 3 cycle
#                [[95, 80, -65, 120, 54], [0, 1, 1, 0]]]

# _______________________________________________________________
#    Curve opt pattrns after bounded alpref
#    opt_ptrn = [[[0.01, 0.01, -23, 0.01, 0.01], [1, 0, 0, 1]],  # 1 cycle
#                [[50, 67, -60, 114, 0.01], [0, 1, 1, 0]]]

#    opt_ptrn = [[[0.01, 0.01, -12, 0.01, 0.01], [1, 0, 0, 1]],  # 2 cycle
#                [[203, 152, -76, 257, 160], [0, 1, 1, 0]]]

#    opt_ptrn = [[[1, 0.01, -7, 0.01, 0.01], [1, 0, 0, 1]],  # 3 cycle *****
#                [[114, 109, -101, 146, 82], [0, 1, 1, 0]]]
