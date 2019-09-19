# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 15:58:50 2019

@author: AmP
"""

import csv
import numpy as np


def generate_pattern(p0, p1, p2, p3, p4, p5, t_move):
    return [p0, p1, p2, p3, p4, p5, 0, 0, False, False, False, False, t_move]


def save_list_as_csv(lis, filename='test.csv'):
     with open(filename, 'w', newline='') as f:
#    with open(filename, 'w') as f:
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


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    ptrn = []
    for p, p_high in zip(np.linspace(0, .9, 101), np.linspace(0, 1, 101)):
        p, p_high = round(p, 2), round(p_high, 2)
        ptrn.append(generate_pattern(p_high, 0, 0, p_high, p_high, 0, t_move=5))
        ptrn.append(generate_pattern(0, 0, 0, 0, 0, 0, t_move=3))
        ptrn.append(generate_pattern(0, p_high, p, 0, 0, p_high, t_move=5))
        ptrn.append(generate_pattern(0, 0, 0, 0, 0, 0, t_move=3))

    t = [0] + list(np.cumsum([p[-1] for p in ptrn]))
    for idx in range(1):
        p1 = [ptrn[0][idx]]+[p[idx] for p in ptrn]
        plt.step(t, p1)

    plt.figure()
    t = list([0]+np.cumsum([p[-1] for p in ptrn]))
    for idx in range(6):
        p1 = [p[idx] for p in ptrn]
        plt.step(t, p1)

    save_list_as_csv(ptrn, 'v40_special1.csv')
