#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 20:07:36 2020

@author: ls
"""

import matplotlib.pyplot as plt
import numpy as np


deg = 5

alp_f = np.array([0, 10, 20, 40, 60, 80, 90, 100])
p_f = np.array([0, .1, .2, .25, .6, .75, .92, 1])

coef = np.polyfit(alp_f, p_f, deg)
clb = list(coef)

coef_s = ['%1.3e' % c for c in coef]

poly = np.poly1d(coef)
alp = np.linspace(min(alp_f)-2, max(alp_f)+2, 100)

plt.figure('CLB')

plt.plot(alp_f, p_f, 'o', label='used measurements')
plt.plot(alp, poly(alp), '-x', label='fitted')

plt.grid()
plt.xlim((-20, 150))
plt.ylim((-.1, 1.3))
plt.xlabel(r'bending angle $\alpha$ ($^\circ$)')
plt.ylabel(r'pressure $p$ (bar)')
plt.legend(loc='lower right')


plt.show()

print(clb)
