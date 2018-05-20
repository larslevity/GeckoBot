# -*- coding: utf-8 -*-
"""
Created on Fri May 18 16:11:13 2018

@author: AmP
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


f_len = 1.2     # factor on length constraint
f_ori = .1     # factor on orientation constraint
blow = .9       # lower stretching bound
bup = 1.1       # upper stretching bound
arc_res = 20    # resolution of arcs


class RobotRepr(object):
    def __init__(self):
        self.len_leg = 1
        self.len_tor = 1.2
        self.state = {'alp1': 10., 'alp2': 1.,
                      'gam': 60., 'bet1': 1., 'bet2': -90.,
                      'F1': True, 'F2': False, 'F3': False, 'F4': False}
        self.meta = {'C1': 90, 'C2': -90, 'C3': 90, 'C4': -90,
                     'l1': self.len_leg, 'l2': self.len_leg,
                     'lg': self.len_tor, 'l3': self.len_leg,
                     'l4': self.len_leg}
        self.coords = {'F1': (0, 0), 'F2': (2*self.len_leg, 0),
                       'F3': (0, -self.len_tor),
                       'F4': (2*self.len_leg, -self.len_tor),
                       'OM': (self.len_leg, 0),
                       'UM': (self.len_leg, -self.len_tor),
                       'R1': (None, None),
                       'R2': (None, None),
                       'R3': (None, None),
                       'R4': (None, None),
                       'RG': (None, None)}

    def get_repr_F1(self):
        c1 = self.meta['C1']
        l1 = self.meta['l1']
        l2 = self.meta['l2']
        l3 = self.meta['l3']
        l4 = self.meta['l4']
        lg = self.meta['lg']
        alp1 = self.state['alp1']
        bet1 = self.state['alp1']
        alp2 = self.state['alp2']
        bet2 = self.state['bet2']
        gam = self.state['gam']
        x1, y1 = self.coords['F1']
        x4, y4 = self.coords['F4']
        xr1, yr1 = self.coords['R1']
        xr2, yr2 = self.coords['R2']
        xr3, yr3 = self.coords['R3']
        xr4, yr4 = self.coords['R4']
        xrg, yrg = self.coords['RG']
        xom, yom = self.coords['OM']
        xum, yum = self.coords['UM']

        x, y = [x1], [y1]
        # draw upper left leg
        xl1, yl1 = calc_arc_coords((x1, y1), c1, c1+alp1,
                                   calc_rad(l1, alp1))
        print 'xy0', x1, y1
        print 'r1', calc_rad(l1, alp1)
        print 'l1', l1
        x = x + xl1
        y = y + yl1
        # draw torso
        xt, yt = calc_arc_coords((x[-1], y[-1]), -90+c1+alp1, -90+c1+alp1+gam,
                                 calc_rad(lg, gam))
        x = x + xt
        y = y + yt
        # draw lower right leg
        xl4, yl4 = calc_arc_coords((x[-1], y[-1]), 90+gam-(90-c1-alp1),
                                   90+gam-(90-c1-alp1)+bet2,
                                   calc_rad(l4, bet2))
        x = x + xl4
        y = y + yl4
        return x, y, ([x1, x4], [y1, y4])
        

    def calcF1F4(self):
        len_leg = self.len_leg
        len_tor = self.len_tor
        x1, y1 = self.coords['F1']
        x4, y4 = self.coords['F4']
        r10 = self.len_leg*360/(2*np.pi*self.state['alp1'])
        rg0 = self.len_tor*360/(2*np.pi*self.state['gam'])
        r40 = self.len_leg*360/(2*np.pi*self.state['bet2'])
        c10 = self.meta['C1']
        c40 = self.meta['C4']
        l10 = calc_len(r10, self.state['alp1'])
        lg0 = calc_len(rg0, self.state['gam'])
        l40 = calc_len(r40, self.state['bet2'])

        # Initial guess
        X0 = np.array([c10, l10, lg0, l40])
        print X0

        def objective(X):
            c1, l1, lg, l4 = X
            c1 = np.mod(c1, 360)
            # calc orientation of foot 4
            c4 = np.mod(180 + self.state['gam'] + self.state['alp1'] -
                        self.state['bet2'] + c1, 360)

            objective = (f_ori*((c1-c10)**2 + (c4-c40)**2) +
                         f_len*((l1-len_leg)**2 + (lg-len_tor)**2 +
                                (l4-len_leg)**2))
            return objective

        def constraint1(X):
            """ F4 should be at the right position """
            _, _, (xf4, yf4), _, _, _ = self.calc_coords_F1F4(X)

            return np.sqrt((x4-xf4)**2 + (y4-yf4)**2)

        bleg = (blow*len_leg, bup*len_leg)
        btor = (blow*len_tor, bup*len_tor)
        bnds = ((0, 360), bleg, btor, bleg)
        con1 = {'type': 'eq', 'fun': constraint1}
        cons = ([con1])
        solution = minimize(objective, X0, method='SLSQP',
                            bounds=bnds, constraints=cons)
        X = solution.x
        print solution
        c4 = np.mod(180 + self.state['gam'] + self.state['alp1'] -
                    self.state['bet2'] + X[0], 360)
        c1, l1, lg, l4 = X
        (xom, yom), (xum, yum), _, (xr1, yr1), (xrg, yrg), (xr4, yr4) = \
            self.calc_coords_F1F4(X)
        # save opt meta data
        self.meta['C1'] = c1
        self.meta['C4'] = c4
        self.meta['l1'] = l1
        self.meta['l4'] = l4
        self.meta['lg'] = lg
        self.coords['OM'] = (xom, yom)
        self.coords['UM'] = (xum, yum)
        self.coords['R1'] = (xr1, yr1)
        self.coords['RG'] = (xrg, yrg)
        self.coords['R4'] = (xr4, yr4)

    def calc_coords_F1F4(self, X):
        """ X = [c1, l1, lg, l4]"""
        x1, y1 = self.coords['F1']
        c1, l1, lg, l4 = X
        r1 = calc_rad(l1, self.state['alp1'])
        rg = calc_rad(lg, self.state['gam'])
        r4 = calc_rad(l4, self.state['bet2'])

        # coords cp upper left leg
        xr1 = x1 + np.cos(np.deg2rad(c1))*r1
        yr1 = y1 + np.sin(np.deg2rad(c1))*r1
        # coords upper torso
        xom = xr1 - np.sin(np.deg2rad(90-c1-self.state['alp1']))*r1
        yom = yr1 - np.cos(np.deg2rad(90-c1-self.state['alp1']))*r1

        # coords cp torso
        xrom = xom + np.cos(np.deg2rad(90-c1-self.state['alp1']))*rg
        yrom = yom - np.sin(np.deg2rad(90-c1-self.state['alp1']))*rg
        # coords lower torso
        xum = xrom - np.cos(np.deg2rad(self.state['gam'] -
                            (90-c1-self.state['alp1'])))*rg
        yum = yrom - np.sin(np.deg2rad(self.state['gam'] -
                            (90-c1-self.state['alp1'])))*rg

        # coords cp lower right foot
        xr4 = xum + np.sin(np.deg2rad(self.state['gam'] -
                           (90-c1-self.state['alp1'])))*r4
        yr4 = yum - np.cos(np.deg2rad(self.state['gam'] -
                           (90-c1-self.state['alp1'])))*r4
        # coords of F4
        xf4 = xr4 + np.sin(np.deg2rad(self.state['bet2'] -
                           (self.state['gam'] -
                            (90-c1-self.state['alp1']))))*r4
        yf4 = yr4 + np.cos(np.deg2rad(self.state['bet2'] -
                           (self.state['gam'] -
                            (90-c1-self.state['alp1']))))*r4
        return ((xom, yom), (xum, yum), (xf4, yf4),
                (xr1, yr1), (xrom, yrom), (xr4, yr4))


def calc_len(radius, angle):
    return angle/360.*2*np.pi*radius


def calc_rad(length, angle):
    return 360.*length/(2*np.pi*angle)


def calc_arc_coords(xy, alp1, alp2, rad):
    """ """
    x0, y0 = xy
    x, y = [x0], [y0]
    xr = x0 + np.cos(np.deg2rad(alp1))*rad
    yr = y0 + np.sin(np.deg2rad(alp1))*rad
    steps = [angle for angle in np.linspace(0, alp2-alp1, arc_res)]
    for dangle in steps:
        x.append(xr - np.sin(np.deg2rad(90-alp1-dangle))*rad)
        y.append(yr - np.cos(np.deg2rad(90-alp1-dangle))*rad)

    return x, y


if __name__ == "__main__":
    
    robrepr = RobotRepr()
    x, y, fp = robrepr.get_repr_F1()
    plt.plot(x, y, 'b*')
    robrepr.calcF1F4()
    x, y, fp = robrepr.get_repr_F1()
    plt.plot(x, y, 'k*')
    #plt.plot(fp, 'k-o')    
    plt.axis('equal')
