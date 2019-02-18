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


def generate_pattern_climb(p0, p1, p2, p3, p4, p5, p6, p7, t_move=3.0,
                           t_fix=.3, t_dfx=.25, stiffener=False):
    p01, p11, p41, p51 = [.25]*4 if stiffener else [.0]*4

    data = [
        [p01, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, False, t_move],  # 0
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, False, True, True, True, t_fix],  # 1
        [0.0, p1, p2, 0.0, p41, 0.0, p6, 0.0, False, True, True, True, t_fix],  # 2
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],  # 3
        [p0, p1, p2, 0.0, p41, p5, p6, 0.0, True, True, True, True, t_fix],  # 4
        [0.0, p1, p2, 0.0, p41, p5, p6, 0.0, True, False, False, True, t_dfx],  # 5

        [p0, p11, 0.0, p3, p4, p51, 0.0, p7, True, False, False, True, t_move],  # 6
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, False, True, True, t_fix],  # 7
        [p0, 0.0, 0.0, p3, 0.0, p51, 0.0, p7, True, False, True, True, t_fix],  # 8
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],  # 9
        [p0, p1, 0.0, p3, p4, p51, 0.0, p7, True, True, True, True, t_fix],  # 10
        [p0, 0.0, 0.0, p3, p4, p51, 0.0, p7, False, True, True, False, t_dfx]  # 11
    ]
    return data


def save_list_as_csv(lis, filename='test.csv'):
    # with open(filename, 'w', newline='') as f:
    with open(filename, 'wb') as f:
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
    print T
    print Tres
    return Ptrn


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    # v4.0
    ptrn = generate_pattern(
            .81, .81, .79, .84, .78, .76, 0, 0, t_move=6, t_fix=.2, t_dfx=.2)

    # v4.0 - 0
    ptrn00 = generate_pattern_2(
            .81, .81, .79, .84, .78, .76, 0, 0, t_move=3, t_fix=.2, t_dfx=.2)

    # v4.0 - 28
    ptrn28 = generate_pattern_2(
            .69, .72, .95, .94, .76, .74, 0, 0, t_move=3, t_fix=.2, t_dfx=.2)

    ptrn48 = generate_pattern_2(
            .62, .65, .98, .97, .73, .71, 0, 0, t_move=3, t_fix=.2, t_dfx=.2)

    ptrn63 = generate_pattern_2(
            .60, .63, .99, .99, .68, .66, 0, 0, t_move=3, t_fix=.2, t_dfx=.2)

    ptrn76 = generate_pattern_climb(
            .60, .63, .9, .9, .68, .66, 0, 0, t_move=3, t_fix=.8, t_dfx=.2)



    Ptrn = resample(ptrn76)

    t = [0] + list(np.cumsum([p[-1] for p in ptrn]))
    for idx in range(1):
        p1 = [ptrn[0][idx]]+[p[idx] for p in ptrn]
        plt.step(t, p1)


    plt.figure()
    t = list([0]+np.cumsum([p[-1] for p in Ptrn]))
    for idx in range(2):
        p1 =  [p[idx] for p in Ptrn]
        plt.step(t, p1)


    save_list_as_csv(ptrn76, 'incl_exp_v40_76.csv')




