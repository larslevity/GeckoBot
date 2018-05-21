# -*- coding: utf-8 -*-
"""
Created on Fri May 18 16:11:13 2018

@author: AmP
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


f_len = 1.     # factor on length constraint
f_ori = .0003     # factor on orientation constraint

blow = .9       # lower stretching bound
bup = 1.1       # upper stretching bound
arc_res = 30    # resolution of arcs


class RobotRepr(object):
    def __init__(self):
        self.len_leg = 1
        self.len_tor = 1.1
        self.state = {'alp1': 0.1, 'alp2': .1,
                      'gam': 90, 'bet1': 90, 'bet2': 90,
                      'F1': True, 'F2': False, 'F3': False, 'F4': False}
        self.meta = {'C1': 45, 'C2': -90, 'C3': 90, 'C4': -90,
                     'l1': self.len_leg, 'l2': self.len_leg,
                     'lg': self.len_tor, 'l3': self.len_leg,
                     'l4': self.len_leg}
        self.coords = {'F1': (0, 0), 'F2': (2*self.len_leg, 0),
                       'F3': (0, -self.len_tor),
                       'F4': (2*self.len_leg, -self.len_tor),
                       'OM': (self.len_leg, 0),
                       'UM': (self.len_leg, -self.len_tor)}
        self.calc_pose()
        self.state['F4'] = True
        self.calc_pose()

    def set_pose(self, pose):
        """ pose = (alp1, bet1, gam, alp2, bet2, F1, F2, F3, F4) """
        alp1, bet1, gam, alp2, bet2, F1, F2, F3, F4 = pose
        self.state['alp1'] = alp1
        self.state['alp2'] = alp2
        self.state['gam'] = gam
        self.state['bet1'] = bet1
        self.state['bet2'] = bet2
        self.state['F1'] = F1
        self.state['F2'] = F2
        self.state['F3'] = F3
        self.state['F4'] = F4
        self.calc_pose()

    def get_coords(self):
        print '\n'
        print 'Coords F1', self.coords['F1']
        print 'Coords F2', self.coords['F2']
        print 'Coords F3', self.coords['F3']
        print 'Coords F4', self.coords['F4']
        print '\n'

    def get_repr(self):
        c1 = self.meta['C1']
        l1 = self.meta['l1']
        l2 = self.meta['l2']
        l3 = self.meta['l3']
        l4 = self.meta['l4']
        lg = self.meta['lg']
        alp1 = self.state['alp1']
        bet1 = self.state['bet1']
        alp2 = self.state['alp2']
        bet2 = self.state['bet2']
        gam = self.state['gam']
        x1, y1 = self.coords['F1']
        x2, y2 = self.coords['F2']
        x3, y3 = self.coords['F3']
        x4, y4 = self.coords['F4']
        xf, yf = [x1, x2, x3, x4],  [y1, y2, y3, y4]
        xom, yom = self.coords['OM']
        xum, yum = self.coords['UM']

        x, y = [x1], [y1]
        # draw upper left leg
        xl1, yl1 = calc_arc_coords((x1, y1), c1, c1+alp1,
                                   calc_rad(l1, alp1))
        x = x + xl1
        y = y + yl1
        # draw torso
        xt, yt = calc_arc_coords((x[-1], y[-1]), -90+c1+alp1, -90+c1+alp1+gam,
                                 calc_rad(lg, gam))
        x = x + xt
        y = y + yt
        # draw lower right leg
        xl4, yl4 = calc_arc_coords((x[-1], y[-1]), -90+gam-(90-c1-alp1),
                                   -90+gam-(90-c1-alp1)-bet2,
                                   calc_rad(l4, bet2))
        x = x + xl4
        y = y + yl4
        # draw upper right leg
        xl2, yl2 = calc_arc_coords((xom, yom), c1+alp1,
                                   c1+alp1+bet1,
                                   calc_rad(l2, bet1))
        x = x + xl2
        y = y + yl2
        # draw lower left leg
        xl3, yl3 = calc_arc_coords((xum, yum), -90+gam-(90-c1-alp1),
                                   -90+gam-(90-c1-alp1)+alp2,
                                   calc_rad(l3, alp2))
        x = x + xl3
        y = y + yl3

        feet = ['F1', 'F2', 'F3', 'F4']
        fp = ([], [])
        nfp = ([], [])
        for idx, foot in enumerate(feet):
            if self.state[foot]:
                fp[0].append(xf[idx])
                fp[1].append(yf[idx])
            else:
                nfp[0].append(xf[idx])
                nfp[1].append(yf[idx])

        return (x, y), fp, nfp

    def calc_pose(self):
        len_leg = self.len_leg
        len_tor = self.len_tor
        x1, y1 = self.coords['F1']
        x4, y4 = self.coords['F4']
        c0 = [self.meta['C1'], self.meta['C2'],
              self.meta['C3'], self.meta['C4']]
        l10 = len_leg
        l20 = len_leg
        lg0 = len_tor
        l30 = len_leg
        l40 = len_leg

        # Initial guess
        X0 = np.array([c0[0], c0[1], l10, l20, lg0, l30, l40])

        def objective(X):
            c1, c2, l1, l2, lg, l3, l4 = X
            c1 = np.mod(c1, 360)
            c2 = np.mod(c2, 360)
            # calc orientation of foot 3 and 4
            c3 = np.mod(180 + self.state['gam'] - self.state['bet1'] +
                        self.state['alp2'] + c2, 360)
            c4 = np.mod(180 + self.state['gam'] + self.state['alp1'] -
                        self.state['bet2'] + c1, 360)
            C = [c1, c2, c3, c4]
            feet = ['F1', 'F2', 'F3', 'F4']
            obj_ori = 0
            for idx, foot in enumerate(feet):
                if self.state[foot]:
                    obj_ori = obj_ori + (C[idx]-c0[idx])
            objective = (f_ori*(obj_ori) +
                         f_len*((l1-len_leg)**2 + (l2-len_leg)**2 +
                                (lg-len_tor)**2 +
                                (l3-len_leg)**2 + (l4-len_leg)**2))
            return objective

        def constraint1(X):
            """ feet should be at the right position """
            if self.state['F1']:
                _, _, (xf1, yf1), (xf2, yf2), (xf3, yf3), (xf4, yf4) = \
                    self.calc_coords_F1(X)
            elif self.state['F2']:
                _, _, (xf1, yf1), (xf2, yf2), (xf3, yf3), (xf4, yf4) = \
                    self.calc_coords_F2(X)
            else:
                AssertionError('Either F1 or F2 or both must be fixed!')
            xf = [xf1, xf2, xf3, xf4]
            yf = [yf1, yf2, yf3, yf4]
            feet = ['F1', 'F2', 'F3', 'F4']
            constraint = 0
            for idx, foot in enumerate(feet):
                if self.state[foot]:
                    constraint = constraint + \
                        np.sqrt((self.coords[foot][0] - xf[idx])**2 +
                                (self.coords[foot][1] - yf[idx])**2)
            return constraint

        bleg = (blow*len_leg, bup*len_leg)
        btor = (blow*len_tor, bup*len_tor)
        bnds = ((0, 360), (0, 360), bleg, bleg, btor, bleg, bleg)
        con1 = {'type': 'eq', 'fun': constraint1}
        cons = ([con1])
        solution = minimize(objective, X0, method='SLSQP',
                            bounds=bnds, constraints=cons)
        X = solution.x
        c1, c2, l1, l2, lg, l3, l4 = X
        c4 = np.mod(180 + self.state['gam'] + self.state['alp1'] -
                    self.state['bet2'] + X[0], 360)
        c3 = np.mod(180 + self.state['gam'] - self.state['bet1'] +
                    self.state['alp2'] + c2, 360)
        (xom, yom), (xum, yum), (xf1, yf1), (xf2, yf2), \
            (xf3, yf3), (xf4, yf4) = \
            self.calc_coords_F1(X)
        # save opt meta data
#        print 'coords: ', self.coords['F3'], 'actual: ', (xf3, yf3)
        print 'constraint function: ', constraint1(X)
        print 'objective function: ', objective(X)
        print 'solution vector: ', X

        self.meta['C1'] = c1
        self.meta['C2'] = c2
        self.meta['C3'] = c3
        self.meta['C4'] = c4
        self.meta['l1'] = l1
        self.meta['l2'] = l2
        self.meta['l3'] = l3
        self.meta['l4'] = l4
        self.meta['lg'] = lg
        self.coords['OM'] = (xom, yom)
        self.coords['UM'] = (xum, yum)
        self.coords['F1'] = (xf1, yf1)
        self.coords['F2'] = (xf2, yf2)
        self.coords['F3'] = (xf3, yf3)
        self.coords['F4'] = (xf4, yf4)

    def calc_coords_F1(self, X):
        """ X = [c1, l1, lg, l4]"""
        xf1, yf1 = self.coords['F1']
        c1, c2, l1, l2, lg, l3, l4 = X
        r1 = calc_rad(l1, self.state['alp1'])
        rg = calc_rad(lg, self.state['gam'])
        r4 = calc_rad(l4, self.state['bet2'])
        r3 = calc_rad(l3, self.state['alp2'])
        r2 = calc_rad(l2, self.state['bet1'])
        alp1 = self.state['alp1']
        alp2 = self.state['alp2']
        gam = self.state['gam']
        bet1 = self.state['bet1']
        bet2 = self.state['bet2']

        # coords cp upper left leg
        xr1 = xf1 + np.cos(np.deg2rad(c1))*r1
        yr1 = yf1 + np.sin(np.deg2rad(c1))*r1
        # coords upper torso
        xom = xr1 - np.sin(np.deg2rad(90-c1-alp1))*r1
        yom = yr1 - np.cos(np.deg2rad(90-c1-alp1))*r1
        # coords cp torso
        xrom = xom + np.cos(np.deg2rad(90-c1-alp1))*rg
        yrom = yom - np.sin(np.deg2rad(90-c1-alp1))*rg
        # coords lower torso
        xum = xrom - np.cos(np.deg2rad(gam - (90-c1-alp1)))*rg
        yum = yrom - np.sin(np.deg2rad(gam - (90-c1-alp1)))*rg
        # coords cp lower right foot
        xr4 = xum + np.sin(np.deg2rad(gam - (90-c1-alp1)))*r4
        yr4 = yum - np.cos(np.deg2rad(gam - (90-c1-alp1)))*r4
        # coords of F4
        xf4 = xr4 + np.sin(np.deg2rad(bet2 - (gam - (90-c1-alp1))))*r4
        yf4 = yr4 + np.cos(np.deg2rad(bet2 - (gam - (90-c1-alp1))))*r4
        # coords cp R3
        xr3 = xum + np.sin(np.deg2rad(gam - (90-c1-alp1)))*r3
        yr3 = yum - np.cos(np.deg2rad(gam - (90-c1-alp1)))*r3
        # coords of F3
        xf3 = xr3 - np.cos(np.deg2rad(-alp2 - gam + 180-c1-alp1))*r3
        yf3 = yr3 + np.sin(np.deg2rad(-alp2 - gam + 180-c1-alp1))*r3
        # coords cp R2
        xr2 = xom + np.cos(np.deg2rad(c1+alp1))*r2
        yr2 = yom + np.sin(np.deg2rad(c1+alp1))*r2
        # coords F2
        xf2 = xr2 + np.sin(np.deg2rad(bet1 - (90-c1-alp1)))*r2
        yf2 = yr2 - np.cos(np.deg2rad(bet1 - (90-c1-alp1)))*r2

        return ((xom, yom), (xum, yum), (xf1, yf1),
                (xf2, yf2), (xf3, yf3), (xf4, yf4))

    def calc_coords_F2(self, X):
        """ X = [c1, l1, lg, l4]"""
        xf2, yf2 = self.coords['F2']
        c1, c2, l1, l2, lg, l3, l4 = X
        r1 = calc_rad(l1, self.state['alp1'])
        rg = calc_rad(lg, self.state['gam'])
        r4 = calc_rad(l4, self.state['bet2'])
        r3 = calc_rad(l3, self.state['alp2'])
        r2 = calc_rad(l2, self.state['bet1'])
        alp1 = self.state['alp1']
        alp2 = self.state['alp2']
        gam = self.state['gam']
        bet1 = self.state['bet1']
        bet2 = self.state['bet2']

        # coords cp upper right leg
        xr2 = xf2 - np.sin(np.deg2rad(c2-90))*r2
        yr2 = yf2 + np.cos(np.deg2rad(c2-90))*r2
        # coords upper torso
        xom = xr2 - np.sin(np.deg2rad(90-c2+bet1))*r2
        yom = yr2 - np.cos(np.deg2rad(90-c2+bet1))*r2
        # coords cp torso
        xrom = xom + np.cos(np.deg2rad(90-c2+bet1))*rg
        yrom = yom - np.sin(np.deg2rad(90-c2+bet1))*rg
        # coords lower torso
        xum = xrom - np.cos(np.deg2rad(gam - (90-c2+bet1)))*rg
        yum = yrom - np.sin(np.deg2rad(gam - (90-c2+bet1)))*rg
        # coords cp lower right foot
        xr4 = xum + np.sin(np.deg2rad(gam - (90-c2+bet1)))*r4
        yr4 = yum - np.cos(np.deg2rad(gam - (90-c2+bet1)))*r4
        # coords of F4
        xf4 = xr4 + np.sin(np.deg2rad(bet2 - (gam - (90-c2+bet1))))*r4
        yf4 = yr4 + np.cos(np.deg2rad(bet2 - (gam - (90-c2+bet1))))*r4
        # coords cp R3
        xr3 = xum + np.sin(np.deg2rad(gam - (90-c2+bet1)))*r3
        yr3 = yum - np.cos(np.deg2rad(gam - (90-c2+bet1)))*r3
        # coords of F3
        xf3 = xr3 - np.cos(np.deg2rad(-alp2 - gam + 180-c2+bet1))*r3
        yf3 = yr3 + np.sin(np.deg2rad(-alp2 - gam + 180-c2+bet1))*r3
        # coords cp R1
        xr1 = xom + np.cos(np.deg2rad(c2-bet1))*r1
        yr1 = yom + np.sin(np.deg2rad(c2-bet1))*r1
        # coords F1
        xf1 = xr1 + np.sin(np.deg2rad(bet1 - (90-c2+alp1)))*r1
        yf1 = yr1 - np.cos(np.deg2rad(bet1 - (90-c2+alp1)))*r1

        return ((xom, yom), (xum, yum), (xf1, yf1),
                (xf2, yf2), (xf3, yf3), (xf4, yf4))


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
#    (x, y), fp, nfp = robrepr.get_repr()
#    plt.plot(x, y, 'b.')

    (x, y), fp, nfp = robrepr.get_repr()
    fpx, fpy = fp
    nfpx, nfpy = nfp
    plt.plot(x, y, 'k.')
    plt.plot(fpx, fpy, 'ko', markersize=10)
    plt.plot(nfpx, nfpy, 'kx', markersize=10)

    poses = []
    poses.append((90, .1, -90, 90, .1, True, False, False, True))
    poses.append((.1, 90, 90, 0.1, 90, False, True, True, False))

    for idx, pose in enumerate(poses):
        col = (.1, .5, float(idx)/len(poses))
        robrepr.set_pose(pose)
        (x, y), fp, nfp = robrepr.get_repr()
        fpx, fpy = fp
        nfpx, nfpy = nfp
        plt.plot(x, y, '.', color=col)
        plt.plot(fpx, fpy, 'o', markersize=10, color=col)
        plt.plot(nfpx, nfpy, 'x', markersize=10, color=col)
        robrepr.get_coords()

    plt.axis('equal')
