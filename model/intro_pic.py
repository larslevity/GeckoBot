# -*- coding: utf-8 -*-
"""
Created on Wed Dec 05 13:00:44 2018

@author: AmP
"""

import matplotlib.pyplot as plt
import kinematic_model_fun as km


if __name__ == "__main__":
    """
    To save the animation you need the libav-tool to be installed:
    sudo apt-get install libav-tools
    """

    init_pose = [(1, 90, 90, 1, 90), 90, (0, 0)]
    ref =      [[[1, 90, -90,1, 90], [1, 0, 1, 1]]
#                [[1, 90, -90, 1, 90], [1, 0, 0, 0]]
#           [[90, 1, 90, 90, 1], [0, 1, 0, 1]]
               ]

    x, r, data, cst = km.predict_pose(ref, init_pose, True, True)
    km.plot_gait(*data)

    if 0:
        fig_ani = plt.figure()
        plt.title('Gecko-robot model animation')
        line_ani = km.animate_gait(fig_ani, *data)

    if 1:
        km.plot_gait(*data)
        km.tikz_interface(*data, name='Pics/intro_/intro_pic5.tex', typ="plain")

    plt.show()


#    init_pose = [(1, 90, 90, 1, 90), 90, (0, 2)]
#    ref =      [[[1, 90, -90, 1, 90], [1, 1, 0, 0]]
#    #           [[90, 1, 90, 90, 1], [0, 1, 1, 0]],
#    #           [[90, 1, 90, 90, 1], [0, 1, 0, 1]]
#               ]
#    
#    x, r, data, cst = km.predict_pose(ref, init_pose, True, True)
#    km.plot_gait(*data)
#
#    if 0:
#        fig_ani = plt.figure()
#        plt.title('Gecko-robot model animation')
#        line_ani = km.animate_gait(fig_ani, *data)
#
#    if 1:
#        km.plot_gait(*data)
#        km.tikz_interface(*data, name='Pics/intro/intro_pic2.tex')