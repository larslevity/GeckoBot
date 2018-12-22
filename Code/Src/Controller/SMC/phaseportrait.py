# -*- coding: utf-8 -*-
"""
Created on Sat Sep 29 12:27:54 2018

@author: ls

y'' + sin(y) = 0

y1' = y2
y2' = -sin(y1)


"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint


def f(Y, t):
    y1, y2 = Y
    return [y2, -np.sin(y1)]

y1 = np.linspace(-2.0, 8.0, 20)
y2 = np.linspace(-2.0, 2.0, 20)

Y1, Y2 = np.meshgrid(y1, y2)

t = 0

u, v = np.zeros(Y1.shape), np.zeros(Y2.shape)

NI, NJ = Y1.shape

for i in range(NI):
    for j in range(NJ):
        x = Y1[i, j]
        y = Y2[i, j]
        yprime = f([x, y], t)
        u[i, j] = yprime[0]
        v[i, j] = yprime[1]


Q = plt.quiver(Y1, Y2, u, v, color='r')

plt.xlabel('$y$')
plt.ylabel('$\dot{y}$')
plt.xlim([-2, 8])
plt.ylim([-4, 4])
plt.savefig('images/phase-portrait.png')

for y20 in [0, 0.5, 1, 1.5, 2, 2.5]:
    tspan = np.linspace(0, 6, 200)
    y0 = [0.0, y20]
    ys = odeint(f, y0, tspan)
    plt.plot(ys[:, 0], ys[:, 1], 'b-')  # path
    plt.plot([ys[0, 0]], [ys[0, 1]], 'bo')   # start
    plt.plot([ys[-1, 0]], [ys[-1, 1]], 'bs')     # end

plt.xlim([-2, 8])
plt.savefig('images/phase-portrait-2.png')
plt.show()
