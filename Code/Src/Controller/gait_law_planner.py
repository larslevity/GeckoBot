# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 11:57:40 2019

@author: AmP
"""

import numpy as np
from scipy.optimize import minimize


DXapprox = {
    'vS11': {
        'ce': [5.4154, -0.0457, -44.1944, -0.0006, 0.778, -0.0832],
        'cx': [0.1106, 0.2225, 11.4146, -0.0008, -17.5133, -0.1213],
        'cy': [1.9498, -0.0682, -3.6997, 0.0004, -0.0333, -0.058]
        }
    }


def evalpoly(q1, q2, c):
    return c[0] + c[1]*q1 + c[2]*q2 + c[3]*q1**2 + c[4]*q2**2 + c[5]*q1*q2


def rotate(vec, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.r_[c*vec[0]-s*vec[1], s*vec[0]+c*vec[1]]


def xbar(xref, xbot, epsbot):
    """ maps the reference point in global COS to robot COS """
    xref = np.array([[xref[0]], [xref[1]]])
    xbot = np.array([[xbot[0]], [xbot[1]]])
    return rotate(xref - xbot, np.deg2rad(-epsbot))


def dx_(x1, x2):  # analytic_model6
    return np.array([
            [.016*x1 - .113*x2**2],
            [-(.044*x2 - .001*x2**2 + .022*x1*x2)]
        ])


def dx(x1, x2, version):  # analytic_model6
    return np.array([
            [evalpoly(x1, x2, DXapprox[version]['cx'])],
            [evalpoly(x1, x2, DXapprox[version]['cy'])]
        ])


def deps_(x1, x2):  # analytic_model6
    return np.deg2rad(-.001*x1 + 10.188*x2 + .019*x2**2 - .936*x1*x2)


def deps(x1, x2, version):
    return np.deg2rad(evalpoly(x1, x2, DXapprox[version]['ce']))


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


def calc_d(xbar, dxval, depsval, n):
    xbar = np.c_[xbar]
    xbar_n = (np.matmul(R(-n*depsval), xbar)
              - np.matmul(sumR(-depsval, n), dxval))
    d = np.linalg.norm(xbar_n)
    return d


def cut(x):
    return x if x > 0.001 else 0.001


def alpha(x1, x2, f, c1=.75):
    alpha = [cut(45 - x1/2. - abs(x1)*x2/2. + x1*x2*c1),
             cut(45 + x1/2. + abs(x1)*x2/2. + x1*x2*c1),
             x1 + x2*abs(x1),
             cut(45 - x1/2. - abs(x1)*x2/2. + x1*x2*c1),
             cut(45 + x1/2. + abs(x1)*x2/2. + x1*x2*c1)
             ]
    return alpha


def Jd(x1, x2, xbar, n, version, h=.001):
    d0 = calc_d(xbar, dx(x1, x2, version), deps(x1, x2, version), n)
    dx1 = calc_d(xbar, dx(x1+h, x2, version), deps(x1+h, x2, version), n)
    dx2 = calc_d(xbar, dx(x1, x2+h, version), deps(x1, x2+h, version), n)
    return np.array([(dx1 - d0)/h, (dx2 - d0)/h]), d0


def find_opt_x(xbar, n, q1bnds, version):
    def objective(x):
        x1, x2 = x
        Jac, d = Jd(x1, x2, xbar, n, version)
        return d, Jac

    x0 = [90, 0]
    bnds = [(q1bnds[0], q1bnds[1]), (-.5, .5)]
    solution = minimize(objective, x0, method='L-BFGS-B', bounds=bnds,
                        jac=True, tol=1e-7)
    return solution.x, objective(solution.x)[0]


def optimal_planner(
        xbar, alp_act, feet_act, lastq1, nmax=2, dist_min=3, q1bnds=[40, 90],
        version='vS11'):

    dist_act = np.linalg.norm(xbar)
    if dist_act < dist_min:
        alp_ref = alp_act
        feet_ref = feet_act
        return [alp_ref, feet_ref], [lastq1, 0]

    feet_ref = [not(foot) for foot in feet_act]
    n = 1
    (x1opt, x2opt), predicted_dist = find_opt_x(xbar, n, q1bnds, version)

    while predicted_dist > dist_act:
        n += 1
        (x1opt, x2opt), predicted_dist = find_opt_x(xbar, n, q1bnds, version)
        print('planning horizon: ', n, 'cycles. predicted dist: ', round(predicted_dist, 2))
        if n > nmax - 1:
            break

    x1opt = -np.sign(lastq1)*x1opt  # switch sign
    alpha_ref = alpha(x1opt, x2opt, feet_ref)

    return [alpha_ref, feet_ref], [x1opt, x2opt]
