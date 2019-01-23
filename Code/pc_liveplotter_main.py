#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 16:56:01 2019

@author: mustapha
"""

from __future__ import print_function

import threading
import time
from termcolor import colored

from Src.Visual.GUI import gtk_gui_v2
from Src.Visual.GUI import datamanagement



# GTK
class GuiThread(threading.Thread):
    def __init__(self, data, task):
        """
        Thread for the GUI provides:
        - visualization of
            - measurements
            - reference signals
            - actuator input signals
        - setting of
            - Controller Gains
            - Maximal Pressure
            - Maximal Ctr Output
            - Tsampling of the BBB (use only if needed)
        *Initialize with:*
        Args:
            - data (datamanagement.GUIRecorder): Container of signal history
            - task (datamanagement.GUITask): Container of task buffer
        """
        threading.Thread.__init__(self)
        self.gui_win = gtk_gui_v2.GeckoBotGUI(data, task)

    def run(self):
        """ run the GUI """
        self.gui_win.run()






def main():
    START_STATE = 'PAUSE'
    (sens_data, rec_u, rec_r, valve_data, dvalve_data, maxpressure,
     maxctrout, tsampling, PID_gains, pattern) = \
        ({'1': 0, '2': 0}, {'u1': 0, 'u2': 0},
         {'r1': 0, 'r2': 0}, ['1', '2', '3', '4', '5', '6'],
         ['1', '2', '3', '4'], .1, 1., .1,
         [[.1 for i in range(3)] for j in range(6)],
         [[0.1]*6+[False]*4+[3.0]]*2)
    
    gui_rec = datamanagement.GUIRecorder()
    gui_task = datamanagement.GUITask(START_STATE, valve_data, dvalve_data,
                                      maxpressure, maxctrout, tsampling,
                                      PID_gains, pattern)
    gui_rec.append(sens_data)
    gui_rec.append(rec_u)
    gui_rec.append(rec_r)
    gui = GuiThread(gui_rec, gui_task)
    gui.start()
    
    gui.join()
    print('all is done')


if __name__ == '__main__':

    main()
