# -*- coding: utf-8 -*-
"""
Created on Wed May 01 13:58:49 2019

@author: AmP
"""
import numpy as np

clb = {
    'vS11': {
        0: [1.377e-06, -2.178e-04, 1.636e-02, 7.900e-02],
        1: [1.798e-06, -3.091e-04, 2.256e-02, -9.096e-02],
        2: [5.349e-07, 7.972e-06, 5.529e-04, 3.766e-01],
        3: [5.447e-07, -4.419e-06, 7.001e-04, 3.619e-01],
        4: [1.049e-06, -1.427e-04, 1.335e-02, -8.880e-02],
        5: [1.328e-06, -1.743e-04, 1.374e-02, 3.609e-02],
        }
    }


def get_pressure(alpha, version='vS11', max_pressure=1):
    pressure = []
    alpha_ = alpha[0:3] + [None] + alpha[3:]

    def cut_off(p):
        if p > max_pressure:
            # Warning('clb pressure > max_presse: I cutted it off')
            p_ = max_pressure
        elif p < 0:
            p_ = 0.00
        else:
            p_ = round(p, 2)
        return p_
    try:
        for idx, alp in enumerate(alpha_):
            if alp is not None:
                if idx == 2:
                    if alp > 0:  # left belly actuated
                        p = eval_poly(clb[version][idx], alp)
                        pressure.append(cut_off(p))
                        pressure.append(.00)  # actuator 3 -> right belly
                    else:  # right belly actuated
                        pressure.append(.00)  # actuator 2 -> left belly
                        p = eval_poly(clb[version][idx+1], abs(alp))
                        pressure.append(cut_off(p))
                else:
                    p = eval_poly(clb[version][idx], alp)
                    pressure.append(cut_off(p))
        return pressure + [0, 0]  # 8 channels
    except KeyError:
        raise NotImplementedError


def eval_poly(coef, x):
    poly = np.poly1d(coef)
    return poly(x)


if __name__ == '__main__':
    alp = [90, 0, -90, 90, 0]
    print('010:', get_pressure(alp))

    alp = [0, 90, 90, 0, 90]
    print('100:', get_pressure(alp))

    alp = [100, 90, -100, 0, 90]
    print('100:', get_pressure(alp, version='vS11'))
