# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 15:58:50 2019

@author: AmP
"""

import csv
import numpy as np


def generate_pattern(p0, p1, p2, p3, p4, p5, p6, p7, t_move=3.0, t_fix=.66,
                     t_dfx=.25, t_hold=.5, stiffener=True):
    p01, p11, p41, p51 = [.25]*4 if stiffener else [.0]*4

    data = [
        [p01, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, False, t_move],
        [p01, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, False, t_hold],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, False, False, True, t_dfx],
        [p0, p11, 0.0, p3, p4, p51, 0.0, p7, True, False, False, True, t_move],
        [p0, p11, 0.0, p3, p4, p51, 0.0, p7, True, False, False, True, t_hold],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, False, True, True, False, t_dfx]
    ]
    return data


def generate_pattern_2(p0, p1, p2, p3, p4, p5, p6, p7, t_move=3.0, t_fix=.66,
                       t_dfx=.25, stiffener=False):
    p01, p11, p41, p51 = [.25]*4 if stiffener else [.0]*4

    data = [
        [p01, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, False, t_move],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, False, False, True, t_dfx],
        [p0, p11, 0.0, p3, p4, p51, 0.0, p7, True, False, False, True, t_move],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, False, True, True, False, t_dfx]
    ]
    return data


def generate_pattern_general(P1, P2, t_move=3.0, t_fix=.66, t_dfx=.25):
    [p0, p1, p2, p3, p4, p5, p6, p7] = P1
    [p00, p11, p22, p33, p44, p55, p66, p77] = P2
    data = [
        [p0, p1, p2, p3, p4, p5, 0.0, 0.0, True, False, False, True, t_move],
        [p0, p1, p2, p3, p4, p5, 0.0, 0.0, True, True, True, True, t_fix],
        [p0, p1, p2, p3, p4, p5, 0.0, 0.0, False, True, True, False, t_dfx],
        [p00, p11, p22, p33, p44, p55, 0, 0, False, True, True, False, t_move],
        [p00, p11, p22, p33, p44, p55, 0, 0, True, True, True, True, t_fix],
        [p00, p11, p22, p33, p44, p55, 0, 0, True, False, False, True, t_dfx]
    ]
    return data



def generate_pattern_climb(p0, p1, p2, p3, p4, p5, p6, p7, t_move=3.0,
                           t_fix=.3, t_dfx=.25, stiffener=False):
    p01, p11, p41, p51 = [.25]*4 if stiffener else [.0]*4

    data = [
        [p01, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, False, t_move],  # 0
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, True, t_fix],  # 1
        [0.0, p1, p2, 0.0, p41, 0.0, p6, 0.0, False, True, True, True, t_fix],  # 2
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],  # 3
        [p0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],  # 4
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],  # 4a
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, False, False, True, t_dfx],  # 5

        [p0, p11, 0.0, p3, p4, p51, 0.0, p7, True, False, False, True, t_move],  # 6
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, False, True, True, t_fix],  # 7
        [p0, 0.0, 0.0, p3, 0.0, p51, 0.0, p7, True, False, True, True, t_fix],  # 8
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],  # 9
        [p0, p1, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],  # 10
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],  # 10a
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, False, True, True, False, t_dfx]  # 11
    ]
    return data


def save_list_as_csv(lis, filename='test.csv'):
    with open(filename, 'w', newline='') as f:
#    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(lis)


def read_list_from_csv(filename):
    out = []
    with open(filename) as f:
        reader = csv.reader(f)
        for row in reader:
            line = []
            for val in row:
                if val == 'True':
                    line.append(True)
                elif val == 'False':
                    line.append(False)
                else:
                    line.append(float(val))
            out.append(line)
    return out


def resample(ptrn, Ts=.1):
    T = sum([p[-1] for p in ptrn])
    Ptrn = []
    for idx in range(len(ptrn)):
        last = ptrn[idx-1][:-1]
        now = ptrn[idx][:-1]
        ptime = ptrn[idx][-1]
        if ptime < Ts:
            Ptrn.append(now + [ptime])
        else:
            num = int(ptime/Ts)
            t = list(np.linspace(Ts, (num+1)*Ts, num, endpoint=False))+[ptime]
            P = {}
            for n, l, jdx in zip(now, last, range(len(now))):
                if isinstance(n, (bool)):
                    P[jdx] = [n]*len(t)
                else:
                    P[jdx] = np.interp(t, [0, ptime], [l, n])
            for jdx, timestep in enumerate(t):
                if np.mod(timestep, Ts) < 1e-1:
                    ref = [round(P[channel][jdx], 2) for channel in P]
                    Ptrn.append(ref + [Ts])
                else:
                    Ptrn.append(now + [round(np.mod(ptime, Ts), 2)])
    Tres = sum([p[-1] for p in Ptrn])
    print(T)
    print(Tres)
    return Ptrn


def get_marker_color():
    return ['red', 'orange', 'darkred', 'blue', 'darkorange', 'darkblue']


def get_act_color():
    return ['red', 'darkred', 'orange', 'darkorange', 'blue', 'darkblue']


def plot_pattern(ptrn, legend=1, linestyle='-'):
    col = get_act_color()
    t = [0] + list(np.cumsum([p[-1] for p in ptrn]))
    for idx in range(6):
        p1 = [ptrn[0][idx]]+[p[idx] for p in ptrn]
        plt.step(t, p1, linestyle, label=idx if legend else None,
                 color=col[idx])
    if legend:
        plt.legend()


def get_ptrn_from_angles(a, version, t=[5, .66, .25], max_prs=1.1):
    p1 = calibration.get_pressure(a[0], version, max_prs)
    p2 = calibration.get_pressure(a[1], version, max_prs)
    ptrn = generate_pattern_general(p1, p2, t[0], t[1], t[2])
    return ptrn


if __name__ == '__main__':
    import sys
    from os import path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

    import matplotlib.pyplot as plt
    from Src.Controller import calibration
    from Src.Controller.gait_law_planner import alpha as gaitlaw


    version = 'v40'
    times = [5, .66, .25]

#    angles = {
#        'straight_1':  [[90, 0, -90, 90, 0], [0, 90, 90, 0, 90]],
#        'straight_2':  [[86, 4, -110, 83, 4], [4, 86, 110, 4, 83]],
#        'straight_3':  [[0, 18, -85, 10, 22], [18, 0, 85, 22, 10]],
#        'curve_1':  [[97, 28, -98, 116, 17], [79, 0, -84, 67, 0]],
#        'curve_2':  [[104, 48, -114, 124, 27], [72, 0, -70, 55, 0]],
#        'curve_3':  [[164, 124, -152, 221, 62], [0, 0, -24, 0, 0]],
#            }
#
#    for key in angles:
#        angle = angles[key]
#        ptrn = get_ptrn_from_angles(angle, version, times)
#        plot_pattern(ptrn)

#        save_list_as_csv(ptrn, key + '.csv')

# %%
    version = 'vS11'
    max_prs = 1.1
    Q1 = [50, 60, 70, 80, 90]
    Q2 = [-.5, -.3, -.1, .1, .3, .5]

    feet1 = [1, 0, 0, 1]
    feet2 = [0, 1, 1, 0]
    times = [2, .25, .25]

    for q1 in Q1:
        for q2 in Q2:
            a1 = gaitlaw(-q1, q2, feet1)
            a2 = gaitlaw(q1, q2, feet2)
            ptrn = get_ptrn_from_angles([a1, a2], version, times, max_prs=max_prs)
#            plt.figure()
#            plot_pattern(ptrn)
            save_list_as_csv(ptrn, version+'/q1_' + str(q1) + 'q2_' + str(q2).replace('.', '') + '.csv')
# %%

    q1 = 80
    q2 = -0.5
    times = [1, .25, .25]
    a1 = gaitlaw(-q1, q2, feet1, c1=1)
    a2 = gaitlaw(q1, q2, feet2, c1=1)
    ptrn = get_ptrn_from_angles([a1, a2], version, times, max_prs=max_prs)
    plt.figure()
    plot_pattern(ptrn, legend=0, linestyle='x')
#    ptrn = resample(ptrn, Ts=.1)
    plot_pattern(ptrn)
    save_list_as_csv(ptrn, version+'/speed_q1_' + str(q1) + 'q2_' + str(q2).replace('.', '') + '.csv')
    


