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

import random


# GTK
class GuiThread(threading.Thread):
    def __init__(self, data):
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
        self.gui_win = gtk_gui_v2.GeckoBotGUI(data)

    def run(self):
        """ run the GUI """
        self.gui_win.run()

    def kill(self):
        self.gui_win.do_delete_event(None, force=True)

    def is_running(self):
        return self.gui_win.is_running


def main():
    def fill_rnd_values():
        def gen_rnd_val():
            rnd = random.randint(0, 100)
            if rnd in range(30):
                return None
            return rnd/100.

        pressure = {'p1': gen_rnd_val(), 'p2': gen_rnd_val()}
        rec_u = {'u1': gen_rnd_val(), 'u2': gen_rnd_val()}
        rec_r = {'r1': gen_rnd_val(), 'r2': gen_rnd_val()}
        timestamp = {'time': time.time()}

        gui_rec.append(pressure)
        gui_rec.append(rec_u)
        gui_rec.append(rec_r)
        gui_rec.append(timestamp)
        time.sleep(.2)

    pressure = {'p1': 0, 'p2': 0}
    rec_u = {'u1': 0, 'u2': 0}
    rec_r = {'r1': 0, 'r2': 0}
    timestamp = {'time': time.time()}

    gui_rec = datamanagement.GUIRecorder()

    gui_rec.append(pressure)
    gui_rec.append(rec_u)
    gui_rec.append(rec_r)
    gui_rec.append(timestamp)
    gui = GuiThread(gui_rec)
    gui.start()

    print('GUI started .. ')
    try:
        print('begin to create rnd samples ...')
        while gui.is_running():
            fill_rnd_values()
            time.sleep(1)
    except KeyboardInterrupt:
        print('keyboard interrupt')
        gui.kill()
    except Exception as err:
        print(err)

    gui.join()
    print('all is done')


if __name__ == '__main__':

    main()
