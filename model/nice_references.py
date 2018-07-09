# -*- coding: utf-8 -*-
"""
Created on Wed Jul 04 14:26:49 2018

@author: AmP

Collection of worth references
"""
import kinematic_model_fun as model
import matplotlib.pyplot as plt


def curve_ptrn():
    f_len = 100.     # factor on length objective
    f_ori = .001  # .0003     # factor on orientation objective
    f_ang = 10     # factor on angle objective
    f = [f_len, f_ori, f_ang]
    init_pose = [[1.0, 1, -7, 1, 1], 90, (0, 3)]
    ptrn_uturn = [[[1, 1, -7, 1, 1], [1, 0, 0, 1]],  # 3 cycle *****
                  [[114, 109, -101, 146, 82], [0, 1, 1, 0]]]

    repr_gait(ptrn_uturn, f, init_pose, 'U-turn')


def straight_ptrn_1():
    f_len = 100.     # factor on length objective
    f_ori = .0001  # .0003     # factor on orientation objective
    f_ang = 10     # factor on angle objective
    f = [f_len, f_ori, f_ang]

#    init_pose = [[.01, 18, -85, .01, 22], 90, (0, 0)]
#    opt_ptrn = [[[.01, 18, -85, .01, 22], [1, 0, 0, 1]],
#                [[18, 0.1, 85, 22, 0.1], [0, 1, 1, 0]]]
    init_pose = [[1, 18, -85, 10, 22], 90, (0, 0)]
    opt_ptrn = [[[1, 18, -85, 10, 22], [1, 0, 0, 1]],
                [[18, 1, 85, 22, 10], [0, 1, 1, 0]]]

    repr_gait(opt_ptrn, f, init_pose, 'straight_f_ori_0001')


def straight_ptrn_2():
    f_len = 100.     # factor on length objective
    f_ori = .01  # .0003     # factor on orientation objective
    f_ang = 10     # factor on angle objective
    f = [f_len, f_ori, f_ang]

    init_pose = [[86, 4, -110, 83, 4], 90, (0, 0)]
    opt_ptrn = [[[86, 4, -110, 83, 4], [1, 0, 0, 1]],  # 5 cycle f_ori=.01
                [[4, 86, 110, 4, 83], [0, 1, 1, 0]]]
    repr_gait(opt_ptrn, f, init_pose, 'straight_f_ori_01')


def straight_ptrn_3():
    f_len = 100.     # factor on length objective
    f_ori = 1  # .0003     # factor on orientation objective
    f_ang = 10     # factor on angle objective
    f = [f_len, f_ori, f_ang]

    init_pose = [[90, 1, -90, 90, 1], 90, (0, 0)]
    opt_ptrn = [[[90, 1, -90, 90, 1], [1, 0, 0, 1]],  # 5 cycle f_ori=10
                [[1, 90, 90, 1, 90], [0, 1, 1, 0]]]
    repr_gait(opt_ptrn, f, init_pose, 'straight_f_ori_1')


def repr_gait(opt_ptrn, f, init_pose, name=''):
    filled_ptrn = model.loop_ptrn(opt_ptrn, n_cycles=2)

    x, r, data, cst = model.predict_pose(filled_ptrn, init_pose, stats=1,
                                         debug=0, f=f)
    model.plot_gait(*data, name='Plot '+name)
    model.tikz_interface(*data, name='Pics/py/'+name+'.tex')

#    plt.figure()
#    plt.plot(cst)
#
#    fig = plt.figure('Animation '+name)
#    lin = model.animate_gait(fig, *data, inv=50)

#    model.save_animation(lin, name='uturn.html', conv='html')



if __name__ == '__main__':
    curve_ptrn()
    straight_ptrn_1()
    straight_ptrn_2()
    straight_ptrn_3()
    plt.show()
