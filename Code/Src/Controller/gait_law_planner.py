# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 11:57:40 2019

@author: AmP
"""

import numpy as np
from scipy.optimize import minimize


def rotate(vec, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.r_[c*vec[0]-s*vec[1], s*vec[0]+c*vec[1]]


def xbar(xref, xbot, epsbot):
    """ maps the reference point in global COS to robot COS """
    xref = np.array([[xref[0]], [xref[1]]])
    xbot = np.array([[xbot[0]], [xbot[1]]])
    return rotate(xref - xbot, np.deg2rad(-epsbot))


def dx(x1, x2):  # analytic_model6
    return np.array([
            [.016*x1 - .113*x2**2],
            [-(.044*x2 - .001*x2**2 + .022*x1*x2)]
        ])


def deps(x1, x2):  # analytic_model6
    return np.deg2rad(-.001*x1 + 10.188*x2 + .019*x2**2 - .936*x1*x2)


def sumsin(x, n):
    return 1/np.sin(x/2)*np.sin((n+1)*x/2)*np.sin(n*x/2)


def sumcos(x, n):
    return 1/np.sin(x/2)*np.sin((n+1)*x/2)*np.cos(n*x/2)


def R(alp):
    return np.array(
            [[np.cos(alp), -np.sin(alp)],
             [np.sin(alp), np.cos(alp)]])


def sumR(alp, n):
    return np.array(
            [[sumcos(alp, n), -sumsin(alp, n)],
             [sumsin(alp, n), sumcos(alp, n)]
             ])


def calc_d(xbar, dx, deps, n):  # Hack
    xbar = np.c_[xbar]
    xbar_n = np.matmul(R(-n*deps), xbar) - np.matmul(sumR(-deps, n), dx)
    d = np.linalg.norm(xbar_n)
    return d


def cut(x):
    return x if x > 0.001 else 0.001


def alpha(x1, x2, f):
    alpha = [cut(45 - x1/2. - abs(x1)*x2/2. + (f[0])*x1*x2),
             cut(45 + x1/2. + abs(x1)*x2/2. + (f[1])*x1*x2),
             x1 + x2*abs(x1),
             cut(45 - x1/2. - abs(x1)*x2/2. + (f[2])*x1*x2),
             cut(45 + x1/2. + abs(x1)*x2/2. + (f[3])*x1*x2)
             ]
    return alpha


def Jd(x1, x2, xbar, n, h=.001):
    d0 = calc_d(xbar, dx(x1, x2), deps(x1, x2), n)
    dx1 = calc_d(xbar, dx(x1+h, x2), deps(x1+h, x2), n)
    dx2 = calc_d(xbar, dx(x1, x2+h), deps(x1, x2+h), n)
    return np.array([(dx1 - d0)/h, (dx2 - d0)/h]), d0


def find_opt_x(xbar, n):
    def objective(x):
        x1, x2 = x
        Jac, d = Jd(x1, x2, xbar, n)
        return d, Jac

    x0 = [90, 0]
    bnds = [(0, 90), (-.5, .5)]
    solution = minimize(objective, x0, method='L-BFGS-B', bounds=bnds,
                        jac=True, tol=1e-7)
    return solution.x


def optimal_planner(xbar, alp_act, feet_act, n=2, dist_min=.1):
    """
    opt planner
    """
    dist_act = np.linalg.norm(xbar)
    if dist_act < dist_min:
        alp_ref = alp_act
        feet_ref = feet_act
        return [alp_ref, feet_ref]

    feet_ref = [not(foot) for foot in feet_act]
    x1opt, x2opt = find_opt_x(xbar, n)
    if alp_act[2] > 0:
        x1opt *= -1
    alpha_ref = alpha(x1opt, x2opt, feet_ref)
    return [alpha_ref, feet_ref]
