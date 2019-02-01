#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 17:01:48 2018

@author: bianca
"""

import time
import cv2
from imutils.video import FPS


from Src.Visual.PiCamera import IMGprocessing as img_proc


def main(testtime=200):

    print("[INFO]detect april tags...")
    vs = PiVideoStream(resolution=(640, 480)).start()
    # allow the camera sensor to warmup
    time.sleep(2.0)

    start = time.time()
    fps = FPS().start()
    try:
        while time.time()-start < testtime:
            # grab the frame from the threaded video stream
            frame = vs.read()

#            img = img_proc.draw_rects(frame)
            # detect pose
            alpha, eps, positions = img_proc.detect_all(frame)

            if alpha is not None:
                print 'alpha:\t', alpha
                print 'eps:\t', eps

                img = img_proc.draw_positions(frame, positions)
            else:
                img = frame

#            pose, ell, bet = img_proc.calc_pose(alpha, eps, positions)
#            img = img_proc.draw_pose(img, pose)

            # display
            cv2.imshow("Frame", img)
            cv2.waitKey(1) & 0xFF

            fps.update()
    finally:
        vs.stop()

    fps.stop()
    cv2.destroyAllWindows()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))



if __name__ == '__main__':
    try:
        from Src.Visual.PiCamera.PiVideoStream import PiVideoStream
        picam = True
    except ImportError:
        import imutils
        picam = False
        print 'No PiCam Found'
        frame = cv2.imread('photo_2019-01-15--14-39-58.jpg', 1)
        frame = imutils.resize(frame, width=700)
        alpha, eps, positions = img_proc.detect_all(frame)
     
        print 'alpha:\t', alpha
        print 'eps:\t', eps
        
        img = img_proc.draw_positions(frame, positions)
        # display
        cv2.imshow("Frame", img)
        cv2.waitKey(0)
        
    
    if picam:
        main()
    
    cv2.destroyAllWindows()

