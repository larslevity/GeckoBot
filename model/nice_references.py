# -*- coding: utf-8 -*-
"""
Created on Wed Jul 04 14:26:49 2018

@author: AmP

Collection of worth references
"""
import kinematic_model_fun as model
import matplotlib.pyplot as plt


init_pose = [[.1, 90, 90, .1, 90], -90, (0, 3)]
ptrn_uturn = [[[1, 0.01, -7, 0.01, 0.01], [1, 0, 0, 1]],  # 3 cycle *****
              [[114, 109, -101, 146, 82], [0, 1, 1, 0]]]

filled_ptrn = model.fill_ptrn(ptrn_uturn, res=10, n_cycles=4)


x, r, data, cst = model.predict_pose(filled_ptrn, init_pose, stats=1, debug=1)
model.plot_gait(*data)

plt.figure()
plt.plot(cst)


fig = plt.figure()
lin = model.animate_gait(fig, *data, inv=50)


model.save_animation(lin, name='uturn.html', conv='html')
plt.show()
