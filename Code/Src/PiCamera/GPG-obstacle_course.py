# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 17:40:22 2020

@author: AmP
"""

if __name__ == '__main__':
    import cv2
    import IMGprocessing

    fname = 'GPG-obstacle_course_src.jpg'
    frame = cv2.imread(fname, 1)

    # measure
    alpha, eps, positions, xref = IMGprocessing.detect_all(frame)
    X1 = (positions[0][1], positions[1][1])
    col = (0, 0, 0)
    IMGprocessing.draw_positions(frame, positions, xref, thick=2, col=col)
    img = IMGprocessing.draw_eps(frame, X1, eps, color=col, dist=70, thick=2)
#        IMGprocessing.draw_pose(frame, alpha, eps, positions, ell0, col=col)

    # correction
#    alpha_opt, eps_opt, positions_opt = \
#        correct_measurement(alpha, eps, positions)
#    col = (10, 100, 200)
#    X1_opt = (positions_opt[0][1], positions_opt[1][1])
#    IMGprocessing.draw_pose(frame, alpha_opt, eps_opt, positions_opt, ell0,
#                            col=col)
#    IMGprocessing.draw_eps(frame, X1_opt, eps_opt, color=col,
#                           dist=50, thick=2)
#    img = IMGprocessing.draw_positions(frame, positions_opt, xref,
#                                       thick=2, col=col)

#    print('coords in main:')
#    print('alp:\t', [round(opt-ori, 2) for ori, opt in zip(alpha, alpha_opt)])
#    print('deps:\t', round(eps_opt - eps, 2))

    cv2.imwrite('GPG-obstacle_course.jpg', img)

    cv2.imshow('frame', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
