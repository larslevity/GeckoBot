# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 15:35:06 2019

@author: AmP
"""


from Src.Visual.GUI import save
import matplotlib.pyplot as plt
import numpy as np


def remove_offset(data):
    start_idx = data['f0'].index(1)  # upper left foot attached 1st time
    start_time = data['time'][start_idx]
    data['time'] = \
        [round(data_time - start_time, 3) for data_time in data['time']]

    succes, jdx = False, 0
    while not succes:
        if not np.isnan(data['x0'][start_idx-jdx]):
            print jdx, data['x0'][start_idx-jdx]
            xstart = data['x0'][start_idx-jdx]
            ystart = data['y0'][start_idx-jdx]
            succes = True
        elif start_idx-jdx < 0:
            xstart, ystart = 0, 0
            break
        else:
            jdx += 1

    for idx in range(6):
        data['x{}'.format(idx)] = [x-xstart for x in data['x{}'.format(idx)]]
        data['y{}'.format(idx)] = [y-ystart for y in data['y{}'.format(idx)]]

    return data


def scale_alpha(data, scale=1/90.):
    for key in data:
        if key[0] == 'a':
            data[key] = [val*scale for val in data[key]]
    return data


def find_cycle_idx(data, cycle=2):
    # r1 jumps from 0 to some value
    p1 = data['r1']
    idx = [i for i, e in enumerate(p1) if e != 0 and p1[i-1] == 0]

    return idx


data_small = save.read_csv("SmallBot_2019_01_28__15_03_38-StartStop.csv")
data_big = save.read_csv("BigBot_walking_cycle.csv")
cycles_small = find_cycle_idx(data_small)
cycles_big = find_cycle_idx(data_big)


data_small = remove_offset(data_small)
data_big = remove_offset(data_big)

data_small = scale_alpha(data_small)
data_big = scale_alpha(data_big)



plt.figure(0)
plt.title('Shift in position')
plt.plot(data_small['time'], data_small['x0'])
plt.plot(data_small['time'], data_small['x2'])
plt.plot(data_small['time'], data_small['x3'])
plt.plot(data_small['time'], data_small['x5'])

plt.plot(data_big['time'], data_big['x0'])
plt.plot(data_big['time'], data_big['x2'])
plt.plot(data_big['time'], data_big['x3'])
plt.plot(data_big['time'], data_big['x5'])

plt.figure(1)
plt.title('Actuation Speed')
n = 30
sidx_B = cycles_big[2]-1
sidx_S = cycles_small[4]-1

plt.grid()

plt.plot(data_small['time'][sidx_S:sidx_S+n], data_big['aIMG1'][sidx_B:sidx_B+n], 'rx-')
plt.plot(data_small['time'][sidx_S:sidx_S+n], data_big['r1'][sidx_B:sidx_B+n], 'r--')
plt.plot(data_small['time'][sidx_S:sidx_S+n], data_big['p1'][sidx_B:sidx_B+n], 'r.-')


plt.plot(data_small['time'][sidx_S:sidx_S+n], data_small['aIMG1'][sidx_S:sidx_S+n], 'bo-')
plt.plot(data_small['time'][sidx_S:sidx_S+n], data_small['r1'][sidx_S:sidx_S+n], 'b--')
plt.plot(data_small['time'][sidx_S:sidx_S+n], data_small['p1'][sidx_S:sidx_S+n], 'b.-')






plt.show()
