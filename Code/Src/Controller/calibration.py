# -*- coding: utf-8 -*-
"""
Created on Wed May 01 13:58:49 2019

@author: AmP
"""
import numpy as np

clb = {
    'vS11': {
        0: [1.367e-10, -3.889e-08, 4.048e-06, -2.128e-04, 1.359e-02, 1.256e-01],
        1: [2.312e-10, -6.387e-08, 6.399e-06, -3.063e-04, 1.448e-02, 1.844e-01],
        2: [1.301e-09, -3.507e-07, 3.155e-05, -1.048e-03, 1.761e-02, 2.219e-01],
        3:  [-2.921e-11, -1.889e-10, 2.836e-07, 6.081e-05, 5.698e-03, 1.441e-01],
        4:  [7.834e-11, -2.904e-08, 4.104e-06, -2.864e-04, 1.725e-02, -4.062e-03],
        5:  [1.797e-10, -6.622e-08, 9.305e-06, -6.456e-04, 2.932e-02, -1.377e-01]
        },
    'vS11_': {
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
                    elif alp == 0:
                        pressure.append(.00)
                        pressure.append(.00)
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
#    alp = [90, 0, -90, 90, 0]
#    print('010:', get_pressure(alp))
#
#    alp = [0, 90, 90, 0, 90]
#    print('100:', get_pressure(alp))

    alp = [45, 45, -50, 45, 45]
    print('100:', get_pressure(alp, version='vS11'))
