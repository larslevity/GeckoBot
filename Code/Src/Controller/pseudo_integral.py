# -*- coding: utf-8 -*-
"""
Created on Tue Sep 25 15:50:22 2018

@author: AmP
"""

import numpy as np
import matplotlib.pyplot as plt


class PseudoIntegrator(object):
    def __init__(self, step=1):
        self.step = step
        self.integ = 0
        self.weight_of_present = 0.005

    def integrate(self, measurement):
        self.integ = (self.integ*(1.-self.weight_of_present)
                      + self.weight_of_present*measurement*self.step)

    def get_integral(self):
        return self.integ

    def reset(self):
        self.integ = 0


step = .001
t = np.arange(0, 1, step)


pressure = [1-1*np.exp(-10*dt) + np.exp(-4*dt)*5*np.sin(dt*2*np.pi) for dt in t]


integrator = PseudoIntegrator(step)
integral = []
for p in pressure:
    arg = p-1. if p-1. > 0 else 0.
    integrator.integrate(arg)
    integral.append(integrator.get_integral())


xc = []
for idx, p in enumerate(pressure):
    if idx != 0:
        if pressure[idx-1] < 1 and p > 1:
            xc.append(t[idx])
        elif pressure[idx-1] > 1 and p < 1:
            xc.append(t[idx])



plt.figure('pressure')
plt.plot(t, pressure)
plt.plot([0, 1], [1, 1], 'k--')
for x in xc:
    plt.plot([x, x], [0, max(pressure)], 'k.-')


plt.figure('integral')
plt.plot(t, integral)
for x in xc:
    plt.plot([x, x], [0, max(integral)], 'k.-')
    
    
    
plt.show()


