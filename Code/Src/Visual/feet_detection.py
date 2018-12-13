# -*- coding: utf-8 -*-
"""
Created on Tue Nov 06 15:43:23 2018

@author: AmP
"""


import numpy as np
import cv2
import imutils


def debug_helper(img, name='img', debug=False):
        if debug:
            cv2.imshow(name, img)
            cv2.waitKey(0)


def detect_circles(filename, debug=False):
    if type(filename) == str:    
        img = cv2.imread(filename, 1)
    else:
        img = filename
    img = imutils.resize(img, width=700)
#    debug_helper(img, debug=debug)
    img = cv2.medianBlur(img, 5)
#    debug_helper(img, debug=debug)

    # detect green:
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#    lower_red = np.array([0, 60, 60])
#    upper_red = np.array([10, 255, 255]) # hsv
#    gray = cv2.inRange(img_hsv, lower_red, upper_red)
    lower_green = np.array([40, 120, 120])
    upper_green = np.array([50, 255, 255]) # hsv
    gray = cv2.inRange(img_hsv, lower_green, upper_green)
    debug_helper(gray, debug=debug)

    # Adaptive Guassian Threshold is to detect sharp edges in the Image.
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 11, 3.5)
    debug_helper(gray, debug=debug)

    kernel = np.ones((3, 3), np.uint8)
    gray = cv2.erode(gray, kernel, iterations=1)
    gray = cv2.dilate(gray, kernel, iterations=1)
    debug_helper(gray, debug=debug)

    # detect circles in the image
#    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=11, minDist=101,  # Works for Picture 1
#                               param1=1,
#                               param2=100, minRadius=0, maxRadius=20)    

    circles = cv2.HoughCircles(gray, cv2.cv.CV_HOUGH_GRADIENT, dp=13, minDist=101,  # works for 2
                               param1=1,
                               param2=100, minRadius=0, maxRadius=20)

    # ensure at least some circles were found
    if circles is not None:
        # sort
        idx_sorted = {i: 0 for i in range(4)}
        if len(list(circles[0, :, 0])) == 4:
            x = list(circles[0, :, 0])
            x_sorted = sorted(x)
            y = list(circles[0, :, 1])
            y_sorted = sorted(y)

            l12 = [y.index(y_sorted[0]), y.index(y_sorted[1])]
            l34 = [y.index(y_sorted[2])]
            y[l34[0]] = np.nan
            l34.append(y.index(y_sorted[3]))
            x12 = list(x)
            x34 = list(x)
            x12[l34[0]] = np.nan
            x12[l34[1]] = np.nan

            idx_sorted[x12.index(min([x[i] for i in l12]))] = 0
            idx_sorted[x12.index(max([x[i] for i in l12]))] = 1
            x34[l12[0]] = np.nan
            x34[l12[1]] = np.nan
            idx_sorted[x34.index(min([x[i] for i in l34]))] = 2
            idx_sorted[x34.index(max([x[i] for i in l34]))] = 3

            centers = [None]*4
        else:
            centers = '{} circles detected'.format(len(list(circles[0, :, 0])))
        # convert the (x, y) coordinates and radius to integers
        circles = np.round(circles[0, :]).astype("int")
        # loop over the (x, y) coordinates and radius of the circles
        for idx, (x, y, r) in enumerate(circles):
            # draw the circle in the output image,
            # then draw a rectangle in the image
            # corresponding to the center of the circle
            cv2.circle(img, (x, y), r, (0, 255, 0), 4)
            cv2.rectangle(img, (x-5, y-5), (x+5, y+5), (0, 128, 255), -1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontscale = .8
            col = (255, 0, 0)

            if type(centers) == list:
                # print x, y, idx, idx_sorted[idx]
                cv2.putText(img, str(idx_sorted[idx]), (x, y-10), font,
                            fontscale, col, 2)
                centers[idx_sorted[idx]] = (x, y, r)
            debug_helper(img, debug=debug)

        return centers, img
    else:
        return None, None


if __name__ == '__main__':
    try:
        import picamera
        import picamera.array
        import time
        picam = True
    except ImportError:
        picam = False
        print 'No PiCam Found'
        img = 'test1.jpg'
    
    if picam:
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            # Start a preview and let the camera warm up for 2 seconds
            camera.start_preview()
            time.sleep(1)
            with picamera.array.PiRGBArray(camera) as stream:
                camera.capture(stream, format='bgr')
                img = stream.array
    
    circs, img = detect_circles(img, debug=True)
    print circs
    cv2.destroyAllWindows()
