# -*- coding: utf-8 -*-
"""
Created on Thu Jun 07 09:51:36 2018

@author: AmP
"""

import numpy as np


#def rotate(vec, angle, axis=1):
#    theta = np.radians(angle)
#    c, s = np.cos(theta), np.sin(theta)
#    if axis == 1:
#        R = np.matrix([[1, 0, 0], [0, c, -s], [0, s, c]])
#    elif axis == 2:
#        R = np.matrix([[c, 0, s], [0, 1, 0], [-s, 0, c]])
#    elif axis == 3:
#        R = np.matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])
#    return R*vec
#
#
#def calc_angle(vec1, vec2, rotate_angle=0.):
#    vec1 = rotate(np.c_[[vec1[0], vec1[1], vec1[2]]], rotate_angle, axis=3)
#    x1, y1, z1 = float(vec1[0]), float(vec1[1]), float(vec1[2])
#    x2, y2, z2 = float(vec2[0]), float(vec2[1]), float(vec2[2])
#
#    l1 = np.linalg.norm([x1, y1, z1])
#    l2 = np.linalg.norm([x2, y2, z2])
#
#    x1, y1, z1 = x1/l1, y1/l1, z1/l1
#    x2, y2, z2 = x2/l2, y2/l2, z2/l2
#
#    z = np.mean([z1, z2])
#
#    phi1 = np.degrees(np.arctan2(y1, x1))
#    vec2 = rotate(np.c_[[x2, y2, 0]], -phi1+90, axis=3)
#
#    phi2 = np.degrees(np.arctan2(float(vec2[1]), float(vec2[0])))
#
#    alpha_IMU = -phi2+90
#
#    if abs(z) > 1:
#        print 'angle is not calculable... z > 1 (arccos(z))'
#        delta = np.nan
#    else:
#        delta = np.degrees(np.arccos(z))
#
#    return alpha_IMU, delta

def calc_angle(vec1, vec2, rotate_angle=0., delta_out=False, jump=np.pi*.5):
    theta = np.radians(rotate_angle)
    vec1 = rotate(vec1, theta)
    x1, y1, z1 = normalize(vec1)
    x2, y2, z2 = normalize(vec2)
    phi1 = np.arctan2(y1, x1)
    vec2 = rotate([x2, y2, 0], -phi1+jump)
    phi2 = np.degrees(np.arctan2(vec2[1], vec2[0]) - jump)

    alpha_IMU = -phi2

    if delta_out:
        z = np.mean([z1, z2])
        delta = np.degrees(np.arccos(z))

    return alpha_IMU if not delta_out else (alpha_IMU, delta)


def normalize(vec):
    x, y, z = vec
    l = np.sqrt(x**2 + y**2 + z**2)
    return x/l, y/l, z/l


def rotate(vec, theta):
    c, s = np.cos(theta), np.sin(theta)
    return (c*vec[0]-s*vec[1], s*vec[0]+c*vec[1], vec[2])
