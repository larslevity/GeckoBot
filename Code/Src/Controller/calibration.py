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
    'vS11___': {  # 19/08/29 obs
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
        },
    'vS11_special2': {  # special 2
        0: [1.5299195708295543e-10, -4.0578986053527206e-08, 3.840307564765325e-06, -0.00016283882151610571, 0.010922822121126488, 0.16845385348259134],
        1: [1.4536386602923124e-10, -5.603948095516581e-08, 7.999020668430735e-06, -0.0005256980610963052, 0.02251386614393631, -0.04185165354838994],
        2: [1.1447568823017596e-09, -2.937148364011541e-07, 2.8265594717713618e-05, -0.0012535626276979125, 0.03197500268216008, 0.028525859256495145],
        3: [1.299719061548217e-09, -2.582844399007761e-07, 1.949822428795414e-05, -0.0007376241023536275, 0.023561757069561828, 0.07212017968250314],
        4: [2.0125332430517237e-10, -5.593336837814883e-08, 5.836613341795258e-06, -0.00030599312904713643, 0.016976911564809655, -0.003367290652079191],
        5: [3.7253202591731913e-10, -1.1635734149985056e-07, 1.3380254048570842e-05, -0.0007057092062811565, 0.024954087815788197, -0.04607502817845186]
        },
    'vS11': {  # special 3
        0: [4.965121562109887e-13, -6.44097132882056e-10, 1.5158359627494762e-07, -3.205605883004579e-05, 0.010052638820931926, 0.134082375974453],
        1: [5.5226508224484436e-11, -2.4185976436640417e-08, 3.8076295002966234e-06, -0.000274055038179612, 0.015949085821324958, -0.02961559405387044],
        2: [9.160037425064399e-10, -3.08455572578132e-07, 3.9453676119984866e-05, -0.002331085055379165, 0.06829721246843559, -0.37656593017926027],
        3: [-1.0393633988836174e-10, 1.765936421017443e-08, 1.6329753165788568e-07, -0.00011664751581913587, 0.011938499721436678, 0.17433420994695759],
        4: [2.89230113993481e-10, -9.113299625275847e-08, 1.0259866988732249e-05, -0.0005220166542632878, 0.02092563431788812, -0.033566176975896325],
        5: [1.6425202957498428e-10, -5.3635789525259444e-08, 6.24097106975067e-06, -0.0003298483624510243, 0.016289891890431146, 0.004707638851766482]
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

        for idx, alp__ in enumerate(alp_):
            plt.figure(idx)
            if idx > 2:
                plt.plot(alp[idx], p[idx+1]*100, 'r.')
            else:
                plt.plot(alp[idx], p[idx]*100, 'r.')
            if idx == 2:
                plt.plot(alp[idx], p[idx+1]*100, 'r.')

            plt.plot(alp[idx], alp__, 'k.')
    for idx, _ in enumerate(alp_):
        plt.figure(idx)
        plt.xlabel('alpha [deg]')
        plt.ylabel('pressure(alpha) [bar*100] / alpha_ [deg]')
        plt.plot(0, 0, 'r.', label='p(alp) * 100')
        plt.plot(0, 0, 'k.', label='alp_(p(alp))')
        plt.legend()
