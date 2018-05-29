# -*- coding: utf-8 -*-
"""
Created on Sun May 27 15:50:36 2018

@author: ls
"""


animate = True

if __name__ == "__main__":
    """
    To save the animation you need the libav-tool to be installed:
    sudo apt-get install libav-tools
    """
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    import matplotlib
    import numpy as np
    from kinematic_model import RobotRepr
    matplotlib.use("Agg")

    robrepr = RobotRepr(f_ori=0.1, f_ang=100, f_len=1)
    robrepr.meta['C1'] = 90
    robrepr.set_pose((.1, .1, .1, .1, .1, True, False, False, False))

    (x, y), fp, nfp = robrepr.get_repr()
    fpx, fpy = fp
    nfpx, nfpy = nfp
    plt.plot(x, y, 'k.')
    plt.plot(fpx, fpy, 'ko', markersize=10)
    plt.plot(nfpx, nfpy, 'kx', markersize=10)

    poses = []

    ''' Circle like gait '''
#    for i in range(14):
#        poses.append((.1, 90, 90, .1, 90, False, True, True, False))
#        poses.append((.1, 90, 90, .1, 90, True, False, False, True))
#        poses.append((5, 45, 45, .1, 45, True, False, False, True))
#        poses.append((10, 0.1, -10, 10, .1, True, False, False, True))
#        poses.append((10, .1, -10, 10, .1, False, True, True, False))
#        poses.append((5, 45, 45, .1, 45, False, True, True, False))
#    poses.append((.1, 90, 90, .1, 90, False, True, True, False))
#    poses.append((.1, 90, 90, .1, 90, True, False, False, True))
#    poses.append((5, 45, 45, .1, 45, True, False, False, True))
#    poses.append((5, 45, 45, .1, 45, False, True, True, False))

    ''' 3 point fixed gait'''
    for i in range(5):
        poses.append((5, 10, -25, 10, 5, True, False, True, True))
        poses.append((10, 20, -50, 20, 10, True, False, True, True))
        poses.append((10, 10, -70, 10, 5, True, True, False, True))
        poses.append((10, .1, -90, .1, .1, True, True, False, True))
        poses.append((50, .1, .1, 0.1, .1, True, True, True, False))
        poses.append((90, .1, 90, 0.1, .1, True, True, True, False))
        poses.append((50, 10, 90, 0.1, .1, False, True, True, True))
        poses.append((10, 20, 90, 0.1, .1, False, True, True, True))
#        poses.append((1, 90, -40, 90, 90, True, False, True, True))
#        poses.append((10, 0.1, -10, 10, .1, True, False, False, True))
#        poses.append((10, .1, -10, 10, .1, False, True, True, False))
#        poses.append((5, 45, 45, .1, 45, False, True, True, False))

    data, data_fp, data_nfp = [], [], []
    for idx, pose in enumerate(poses):
        print '\n\nPOSE ', idx, '\n'
        col = (.1, .5, float(idx)/len(poses))
        robrepr.set_pose(pose)
        (x, y), fp, nfp = robrepr.get_repr()
        fpx, fpy = fp
        nfpx, nfpy = nfp
        plt.plot(x, y, '.', color=col)
        plt.plot(fpx, fpy, 'o', markersize=15, color=col)
        plt.plot(nfpx, nfpy, 'x', markersize=10, color=col)
        robrepr.get_coords()
        data.append((x, y))
        data_fp.append((fpx, fpy))
        data_nfp.append((nfpx, nfpy))

    plt.axis('equal')

    # Animation
    if animate:
        def update_line(num, data, line, data_fp, line_fp, data_nfp, line_nfp):
            x, y = data[num]
            fpx, fpy = data_fp[num]
            nfpx, nfpy = data_nfp[num]
            line.set_data(np.array([[x], [y]]))
            line_fp.set_data(np.array([[fpx], [fpy]]))
            line_nfp.set_data(np.array([[nfpx], [nfpy]]))
            return line, line_fp, line_nfp

        fig1 = plt.figure()

        n = len(poses)
        l, = plt.plot([], [], '.')
        lfp, = plt.plot([], [], 'o', markersize=15)
        lnfp, = plt.plot([], [], 'x', markersize=10)
        plt.xlim(-2, 6)
        plt.ylim(-4, 3)
    #    plt.axis('equal')
        plt.title('Gecko-robot model walking a circle')
        line_ani = animation.FuncAnimation(fig1, update_line, n,
                                           fargs=(data, l, data_fp, lfp,
                                                  data_nfp, lnfp),
                                           interval=300, blit=True)
        plt.show()

        # Set up formatting for the movie files
        Writer = animation.writers['avconv']
        writer = Writer(fps=15, metadata=dict(artist='Lars Schiller'),
                        bitrate=1800)
        line_ani.save('gait.mp4', writer=writer)
