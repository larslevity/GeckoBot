#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 13:43:41 2018

@author: mustapha
"""

#import numpy as np
import logging
import numpy as np




logPath = "."
fileName = 'testlog'

logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.ERROR)


fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


for i in range(10):
    x = '{}'.format(4)
    rootLogger.info('Hallo debug')
#    y = np.zeros(6)

rootLogger.info('Hallo debug')



def rotate(vec, angle, axis=1):
    theta = np.radians(angle)
    c, s = np.cos(theta), np.sin(theta)
    if axis == 1:
        R = np.matrix([[1, 0, 0], [0, c, -s], [0, s, c]])
    elif axis == 2:
        R = np.matrix([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    elif axis == 3:
        R = np.matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return R*vec


def calc_angle(vec1, vec2, rotate_angle=0.):
    vec1 = rotate(np.c_[[vec1[0], vec1[1], vec1[2]]], rotate_angle, axis=3)
    x1, y1, z1 = float(vec1[0]), float(vec1[1]), float(vec1[2])
    x2, y2, z2 = float(vec2[0]), float(vec2[1]), float(vec2[2])

    l1 = np.linalg.norm([x1, y1, z1])
    l2 = np.linalg.norm([x2, y2, z2])

    x1, y1, z1 = x1/l1, y1/l1, z1/l1
    x2, y2, z2 = x2/l2, y2/l2, z2/l2

#    z = np.mean([z1, z2])

    phi1 = np.degrees(np.arctan2(y1, x1))
    vec2 = rotate(np.c_[[x2, y2, 0]], -phi1+90, axis=3)

    phi2 = np.degrees(np.arctan2(float(vec2[1]), float(vec2[0])))

    alpha_IMU = -phi2+90

#    if abs(z) > 1:
#        print 'angle is not calculable... z > 1 (arccos(z))'
#        delta = np.nan
#    else:
#        delta = np.degrees(np.arccos(z))

    return alpha_IMU


def calc_angle2(vec1, vec2, rotate_angle=0., delta_out=False):
    theta = np.radians(rotate_angle)
    vec1 = rotate2(vec1, theta)
    x1, y1, z1 = normalize(vec1)
    x2, y2, z2 = normalize(vec2)
    phi1 = np.arctan2(y1, x1)
    vec2 = rotate2([x2, y2, 0], -phi1+np.pi*.5)
    phi2 = np.degrees(np.arctan2(vec2[1], vec2[0]))

    alpha_IMU = -phi2+90

    if delta_out:
        z = np.mean([z1, z2])
        delta = np.degrees(np.arccos(z))

    return alpha_IMU if not delta_out else (alpha_IMU, delta)

def normalize(vec):
    x, y, z = vec
    l = np.sqrt(x**2 + y**2 + z**2)
    return x/l, y/l, z/l

def rotate2(vec, theta):
    c, s = np.cos(theta), np.sin(theta)
    return (c*vec[0]-s*vec[1], s*vec[0]+c*vec[1], vec[2])


def main():
    vec1 = [.32222222222222222, .41111111111111111, .522222222222222]
    vec2 = [.4555555555, .35555555555555, .55555555555555555]
    for i in range(1000):    
        alpha  = calc_angle(vec1, vec2, 34)
        alpha2 = calc_angle2(vec1, vec2, 34)
    print alpha , alpha2


if __name__ == "__main__":
    main()

