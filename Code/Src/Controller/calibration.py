# -*- coding: utf-8 -*-
"""
Created on Wed May 01 13:58:49 2019

@author: AmP
"""
import numpy as np

clb = {
    'vS11__': {  # obs
        0: [1.367e-10, -3.889e-08, 4.048e-06, -2.128e-04, 1.359e-02, 1.256e-01],
        1: [2.312e-10, -6.387e-08, 6.399e-06, -3.063e-04, 1.448e-02, 1.844e-01],
        2: [1.301e-09, -3.507e-07, 3.155e-05, -1.048e-03, 1.761e-02, 2.219e-01],
        3:  [-2.921e-11, -1.889e-10, 2.836e-07, 6.081e-05, 5.698e-03, 1.441e-01],
        4:  [7.834e-11, -2.904e-08, 4.104e-06, -2.864e-04, 1.725e-02, -4.062e-03],
        5:  [1.797e-10, -6.622e-08, 9.305e-06, -6.456e-04, 2.932e-02, -1.377e-01]
        },
    'vS11': {  # 19/08/29
        0: [7.763918467045786e-10, -1.9007911865706754e-07, 1.6895216480386433e-05, -0.000696563913475042, 0.021529285790052623, 0.23729962302436852], 
        1: [-1.1688003355907625e-10, 3.262228762381627e-08, -2.479689050235238e-06, -5.030531828913613e-05, 0.017871793507729074, -0.02836710904370858],
        2: [1.4753156893859107e-09, -4.1032286775496736e-07, 4.395107966462804e-05, -0.002288177323864942, 0.0651863088464759, -0.24033325008363748],
        3: [3.28851379579006e-10, -1.3101616601789867e-08, -1.4505721223874318e-06, -0.0001138264865738512, 0.02236886220859973, 0.18422120223542174],
        4: [-1.948911557272794e-10, 6.382994990316917e-08, -7.3479601030375875e-06, 0.000307174954829839, 0.006590962193495432, 0.1040994925240043],
        5: [-1.8490676560567495e-10, 4.378316342430727e-08, -2.5890573328546297e-06, -9.65241955393128e-05, 0.01929378679667815, 0.030656864422897872]},
    'vS11_': {  # obs
        0: [1.377e-06, -2.178e-04, 1.636e-02, 7.900e-02],
        1: [1.798e-06, -3.091e-04, 2.256e-02, -9.096e-02],
        2: [5.349e-07, 7.972e-06, 5.529e-04, 3.766e-01],
        3: [5.447e-07, -4.419e-06, 7.001e-04, 3.619e-01],
        4: [1.049e-06, -1.427e-04, 1.335e-02, -8.880e-02],
        5: [1.328e-06, -1.743e-04, 1.374e-02, 3.609e-02],
        }
    }


def get_pressure(alpha, version, max_pressure=1):
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


def get_alpha(pressure, version):
    pressure = pressure[:6]  # 6 clbs
    sign_alp = -1 if pressure[2] == 0 else 1

    alp = []
    for idx, p in enumerate(pressure):
        coeff = clb[version][idx]
        poly = np.poly1d(coeff)
        roots = (poly - p).roots
        roots = roots[~np.iscomplex(roots)].real
        roots = roots[roots > 0]
        roots = roots[roots < 120]
        if len(roots) == 1:
            alp.append(roots[0])
        elif len(roots) == 0:
            alp.append(0)
        else:
            alp.append(np.mean(roots))
    if sign_alp < 0:
        alp = alp[:2] + alp[-3:]
    else:
        alp = alp[:3] + alp[-2:]
    alp[2] *= sign_alp

    return alp


def eval_poly(coef, x):
    if x < 0:
        return 0
    else:
        poly = np.poly1d(coef)
        return poly(x)


if __name__ == '__main__':
    from matplotlib import pyplot as plt

    version = 'vS11'

    alp = [30, 45, -100, 45, 45]
    print('alp:\t', alp)
    p = get_pressure(alp, version=version)
    print('p:\t', p)
    alp_ = get_alpha(p, version)
    print('alp_:\t', [round(a) for a in alp_])

    alp = [30, 45, 100, 45, 45]
    print('\nalp:\t', alp)
    p = get_pressure(alp, version=version)
    print('p:\t', p)
    alp_ = get_alpha(p, version)
    print('alp_:\t', [round(a) for a in alp_])


    for alpha in np.linspace(-120, 120, 50):
        alp = [alpha]*5
        p = get_pressure(alp, version=version)
        alp_ = get_alpha(p, version)

        for idx, pp in enumerate(alp_):
            plt.figure(idx)
            if idx > 2:
                plt.plot(alp[idx], p[idx+1]*100, 'r.', label='p(alp) * 100')
            else:
                plt.plot(alp[idx], p[idx]*100, 'r.', label='p(alp) * 100')
            if idx == 2:
                plt.plot(alp[idx], p[idx+1]*100, 'r.', label='p(alp) * 100')

            plt.plot(alp[idx], pp, 'k.', label='alp(p)')
