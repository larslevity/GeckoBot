# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 15:35:06 2019

@author: AmP
"""


from Src.Visual.GUI import save
import matplotlib.pyplot as plt
import numpy as np


def remove_offset_time_xy(data):
    start_idx = data['f0'].index(1)  # upper left foot attached 1st time
    start_time = data['time'][start_idx]
    data['time'] = \
        [round(data_time - start_time, 3) for data_time in data['time']]

    succes, jdx = False, 0
    while not succes:
        if not np.isnan(data['x0'][start_idx-jdx]):
#            print jdx, data['x0'][start_idx-jdx]
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


def find_cycle_idx(data):
    # r1 jumps from 0 to some value
    p1 = data['r1']
    idx = [i for i, e in enumerate(p1) if e != 0 and p1[i-1] == 0]

    return idx


def rm_offset(lis):
    offset = lis[0]
    return [val-offset for val in lis]


def calc_mean_stddev(mat):
    mu1 = np.nanmean(mat, axis=1)
#    mu1 = mat.mean(axis=1)
#    sigma1 = mat.std(axis=1)
    sigma1 = np.nanstd(mat, axis=1)
    return mu1, sigma1


def make_matrix(data, cycle_idx):
    start = [cycle_idx[idx]-1 for idx in range(len(cycle_idx)-1)]
    stop = [cycle_idx[idx+1] for idx in range(len(cycle_idx)-1)]
    lens = [sto-sta for sta, sto in zip(start, stop)]
    nSteps = min(lens)
    min_idx = lens.index(nSteps)
    nSets = len(lens)

    mat = np.ndarray((nSteps, nSets))
    for set_ in range(nSets):
        for step in range(nSteps):
            mat[step][set_] = data[start[set_]+step]
    return mat, min_idx



"""
________________________________________________
____________________Load Data____________
________________________________________________
"""

data_small = save.read_csv("SmallBot_1.csv")
data_big = save.read_csv("BigBot_walking_cycle_1.csv")
cycles_small = find_cycle_idx(data_small)
cycles_big = find_cycle_idx(data_big)


data_small = remove_offset_time_xy(data_small)
data_big = remove_offset_time_xy(data_big)

#data_small = scale_alpha(data_small)
#data_big = scale_alpha(data_big)



"""
________________________________________________
____________________Actuation Speed_Small____________
________________________________________________
"""

color_prs = 'darkslategray'
color_ref = 'lightcoral'
color_alp = 'red'



fig, ax_prs = plt.subplots()
ax_alp = ax_prs.twinx()
ax_prs.set_xlabel('time (s)')
ax_prs.set_ylabel('pressure (bar)', color=color_prs)
ax_prs.tick_params('y', colors=color_prs)
ax_alp.set_ylabel('angle (deg)', color=color_alp)
ax_alp.tick_params('y', colors=color_alp)



# Angle Plot
matS, min_idx = make_matrix(data_small['aIMG1'], cycles_small[1:])
mu, sigma = calc_mean_stddev(matS)

# time
sidx_S = cycles_small[min_idx+1]-1
stop_S = cycles_small[min_idx+2]
t = rm_offset(data_small['time'][sidx_S:stop_S])

# Angle Plot --cont.
ax_alp.plot(t, mu, '-', lw=2, label='alpha_{v1}', color=color_alp)
ax_alp.fill_between(t, mu+sigma, mu-sigma, facecolor=color_alp, alpha=0.5)

# Pressure Plot
mat, _ = make_matrix(data_small['p1'], cycles_small[1:])
mu, sigma = calc_mean_stddev(mat)
ax_prs.plot(t, mu, '-', lw=2, label='p_{v1}', color=color_prs)
ax_prs.fill_between(t, mu+sigma, mu-sigma, facecolor=color_prs, alpha=0.5)

# Reference Plot
ax_prs.plot(t, data_small['r1'][sidx_S:stop_S], '--', color=color_ref, label='ref_{v1}')    

########## BIG BOT


# Index
sidx_B = cycles_big[4]-1
stop_B = cycles_big[4+1]

t = rm_offset(data_big['time'][sidx_B:stop_B])

# Angle Plot
mat, _ = make_matrix(data_big['aIMG1'], cycles_big[1:])
mu, sigma = calc_mean_stddev(mat)
ax_alp.plot(t, mu, ':', lw=2, label='alpha_{v0}', color=color_alp)
ax_alp.fill_between(t, mu+sigma, mu-sigma, facecolor=color_alp, alpha=0.2)

# Pressure Plot
mat, _ = make_matrix(data_big['p1'], cycles_big[1:])
mu, sigma = calc_mean_stddev(mat)
ax_prs.plot(t, mu, ':', lw=2, label='p_{v0}', color=color_prs)
ax_prs.fill_between(t, mu+sigma, mu-sigma, facecolor=color_prs, alpha=0.2)

# Reference Plot
ax_prs.plot(t, data_big['r1'][sidx_B:stop_B], '-.', color=color_ref, label='ref_{v0}')    

## Legend
ax_prs.legend(loc='upper right')
ax_alp.legend(loc='right')
ax_prs.grid()
fig.tight_layout()

plt.savefig('pics/actuation_speed.png', dpi=500, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None, metadata=None)




"""
________________________________________________
____________________Shift in Position___________
________________________________________________
"""

plt.figure()
plt.title('Shift in position')

ds, db, cyc_small, cyc_big = [], [], [], []
for exp in range(1,4):
    data_small = save.read_csv("SmallBot_{}.csv".format(exp))
    data_big = save.read_csv("BigBot_walking_cycle_{}.csv".format(exp))
    cycles_small = find_cycle_idx(data_small)
    cycles_big = find_cycle_idx(data_big)
    data_small = remove_offset_time_xy(data_small)
    data_big = remove_offset_time_xy(data_big)

    ds.append(data_small)
    db.append(data_big)
    cyc_small.append(cycles_small)
    cyc_big.append(cycles_big)

    
    plt.plot(data_small['time'], data_small['x0'])


min_dist_big = min([idx[-1] - idx[0] for idx in cyc_big])



def calc_centerpoint(data_set, cycles):
    X = []
    min_dist = min([idx[-1] - idx[0] for idx in cycles])

    for exp in range(len(data_set)):
        start = cycles[exp][0]
        x = []  # list of center in current exp
        for idx in range(start, start+min_dist):
            all_x = [data_set[exp][foot][idx] for foot in ['x0', 'x2', 'x3', 'x5']]  # calc center
            x.append(np.nanmean(all_x))
        X.append(x)     # List of centers in all exp
    return X



def make_matrix_plain(data):
    nSteps = len(data[0])
    nSets = len(data)
    mat = np.ndarray((nSteps, nSets))
    for set_ in range(nSets):
        for step in range(nSteps):
            mat[step][set_] = data[set_][step]
    return mat




plt.figure()
for row in calc_centerpoint(ds, cyc_small):
    plt.plot(row)

plt.figure()

## small
centers = calc_centerpoint(ds, cyc_small)
mat = make_matrix_plain(centers)
mu, sigma = calc_mean_stddev(mat)
# calc t
plt.plot(range(len(mu)), mu, ':', lw=2, label='p_{v0}', color=color_prs)
plt.fill_between(range(len(mu)), mu+sigma, mu-sigma, facecolor=color_prs, alpha=0.2)


## big
centers = calc_centerpoint(db, cyc_big)
mat = make_matrix_plain(centers)
mu, sigma = calc_mean_stddev(mat)
# calc t
plt.plot(range(len(mu)), mu, ':', lw=2, label='p_{v0}', color=color_alp)
plt.fill_between(range(len(mu)), mu+sigma, mu-sigma, facecolor=color_alp, alpha=0.2)



#plt.plot(x)
#    plt.plot(ds[exp]['x0'][start:start+min_dist_small])


#plt.plot(data_small['time'], data_small['x0'])
#plt.plot(data_small['time'], data_small['x2'])
#plt.plot(data_small['time'], data_small['x3'])
#plt.plot(data_small['time'], data_small['x5'])

#plt.plot(data_big['time'], data_big['x0'])
#plt.plot(data_big['time'], data_big['x2'])
#plt.plot(data_big['time'], data_big['x3'])
#plt.plot(data_big['time'], data_big['x5'])




plt.show()
