# -*- coding: utf-8 -*-
"""
Created on Sun May 27 15:50:36 2018

@author: ls
"""

from scipy.optimize import minimize
from scipy.optimize import basinhopping


animate = True
save = False


def flat_list(l):
    return [item for sublist in l for item in sublist]


def gnerate_ptrn(X):
    n_cycles = len(X)/10
    ptrn = []
    for n in range(n_cycles):
        p = X[n*10:n*10+10]
        ptrn.append((p[0], p[1], p[2], p[3], p[4], True, False, False, True))
        ptrn.append((p[5], p[6], p[7], p[8], p[9], False, True, True, False))
    return ptrn


def optimize_gait(robrepr, n_cycles, initial_pose):
    obj_history = []
    bleg = (0.1, 120)
    btor = (-120, 120)
    bnds, X0 = [], []
    for n in range(n_cycles):
        bnds.append([bleg, bleg, btor, bleg, bleg,
                     bleg, bleg, btor, bleg, bleg])
        X0.append([90, .1, -90, 90, .1,
                   .1, .1, .1, .1, .1])
    bnds = flat_list(bnds)
    X0 = flat_list(X0)

    def objective_straight(X):
        ptrn = gnerate_ptrn(X)
        robrepr.set_initial_pose(*initial_pose)
        data, data_fp, data_nfp, _ = process_pattern(ptrn, robrepr)
#        print data_fp
        obj = 0
        for fp, nfp in zip(data_fp, data_nfp):
            xfp, yfp = fp
            xnfp, ynfp = nfp
            obj += sum(yfp)  # + sum(ynfp)
        print -obj, '\n', ptrn[0], '\n', ptrn[1]
        return -obj

    def constraint(X):
        return 0

    def objective_curve(X):
        ptrn = gnerate_ptrn(X)
        robrepr.set_initial_pose(*initial_pose)
        data, data_fp, data_nfp, _, eps = process_pattern(ptrn, robrepr)
        obj = eps[-1]
        obj_history.append(obj)
        print 'step', len(obj_history), '\t', obj
        return obj

    def constraint_curve(X):
        return 0

    con = {'type': 'eq', 'fun': constraint}
    kwargs = dict(method='L-BFGS-B', bounds=bnds, constraints=con)
#    solution = basinhopping(objective_straight, X0, minimizer_kwargs=kwargs)
#    solution = minimize(objective_straight, X0,
#                        method='L-BFGS-B', bounds=bnds, constraints=con)
#    solution = minimize(objective_curve, X0,
#                        method='L-BFGS-B', bounds=bnds, constraints=con)
#    solution = basinhopping(objective_curve, X0, minimizer_kwargs=kwargs)
    solution = minimize(objective_curve, X0,
                        method='COBYLA', bounds=bnds)
    X = solution.x
    ptrn = gnerate_ptrn(X)
    return ptrn, obj_history


def animate_gait(data, data_fp, data_nfp, fig1):
    def update_line(num, data, line, data_fp, line_fp, data_nfp, line_nfp):
        x, y = data[num]
        fpx, fpy = data_fp[num]
        nfpx, nfpy = data_nfp[num]
        line.set_data(np.array([[x], [y]]))
        line_fp.set_data(np.array([[fpx], [fpy]]))
        line_nfp.set_data(np.array([[nfpx], [nfpy]]))
        return line, line_fp, line_nfp

    n = len(poses)
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
        interval=300, blit=True)
    return line_ani


def plot_gait(data, data_fp, data_nfp):
    for idx in range(len(data)):
        (x, y) = data[idx]
        (fpx, fpy) = data_fp[idx]
        (nfpx, nfpy) = data_nfp[idx]
        c = (1-float(idx)/len(poses))*.8
        col = (c, c, c)
        print c
        plt.plot(x, y, '.', color=col)
        plt.plot(fpx, fpy, 'o', markersize=10, color=col)
        plt.plot(nfpx, nfpy, 'x', markersize=10, color=col)
        print idx, fpy
        print idx, nfpy
    plt.axis('equal')


def save_animation(line_ani, name='gait.mp4'):
    # Set up formatting for the movie files
    Writer = animation.writers['avconv']
    writer = Writer(fps=15, metadata=dict(artist='Lars Schiller'),
                    bitrate=1800)
    line_ani.save(name, writer=writer)


def process_pattern(poses, robrepr):
    data, data_fp, data_nfp, costs, eps = [], [], [], [], []
    for idx, pose in enumerate(poses):
        print '\n\nPOSE ', idx, '\n'
        objj = robrepr.set_pose(pose)
        (x, y), (fpx, fpy), (nfpx, nfpy), epss = robrepr.get_repr()
        costs.append(objj)
        data.append((x, y))
        data_fp.append((fpx, fpy))
        data_nfp.append((nfpx, nfpy))
        eps.append(epss)
    return data, data_fp, data_nfp, costs, eps


if __name__ == "__main__":
    """
    To save the animation you need the libav-tool to be installed:
    sudo apt-get install libav-tools
    """
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    import numpy as np
    from kinematic_model import RobotRepr

    robrepr = RobotRepr(f_ori=0.001, f_ang=100, f_len=.1)
    initial_pose = (45, 45, .1, 45, 45, 90)
    robrepr.set_initial_pose(*initial_pose)

#    poses = []
#    poses.append(((30, 10, 10, 30, 10, True, True, True, True)))
#    poses.append(((1, 60, 90, 1, 10, True, True, True, True)))
#
###    ''' Circle like gait '''
#    for i in range(14):
#        poses.append((.1, 90, 90, .1, 90, False, True, True, False))
#        poses.append((.1, 90, 90, .1, 90, True, False, False, True))
#        poses.append((5, 45, 45, .1, 45, True, False, False, True))
#        poses.append((10, 0.1, -10, 10, .1, True, False, False, True))
#        poses.append((10, .1, -10, 10, .1, False, True, True, False))
#        poses.append((5, 45, 45, .1, 45, False, True, True, False))
#    poses.append((.1, 90, 90, .1, 90, False, True, True, False))
#    poses.append((.1, 90, 90, .1, 90, True, False, False, True))
#    poses.append((5, 45, 45, .1, 45, True, False, False, True))
#    poses.append((5, 45, 45, .1, 45, False, True, True, False))
#
###    ''' 3 point fixed gait'''
#    for i in range(2):
#        poses.append(( 5, 50, -25, 10,  5, True, False, True, True))
#        poses.append((10, 20, -90, 20, 10, True, False, True, True))
#        poses.append((10, 50, -70, 10,  5, True, True, False, True))
#        poses.append((10, 10, -90, .1, .1, True, True, False, True))
#        poses.append((50,  5,  25,  5, 10, True, True, True, False))
#        poses.append((20, 10,  90, 10, 20, True, True, True, False))
#        poses.append((50, 10,  70,  5, 10, False, True, True, True))
#        poses.append((10, 10,  90, .1, .1, False, True, True, True))
#
    poses, obj_history = optimize_gait(robrepr, 2, initial_pose)
    robrepr.set_initial_pose(*initial_pose)
#    gait = flat_list([[initial_pose], poses])
    data, data_fp, data_nfp, costs, _ = process_pattern(poses, robrepr)
    print data_fp

    fig_plot = plt.figure()
#    plt.hold()
    plt.title('Gecko-robot model plot')
    plot_gait(data, data_fp, data_nfp)

    fig_obj = plt.figure()
    plt.title('Costs or "Stress" inside the robot')
    plt.plot(costs)

    fig_objhist = plt.figure()
    plt.title('Objective history')
    plt.plot(obj_history)

    if animate:
        fig_ani = plt.figure()
        plt.title('Gecko-robot model animation')
        line_ani = animate_gait(data, data_fp, data_nfp, fig_ani)

    plt.show()
