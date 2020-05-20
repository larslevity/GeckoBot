#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 17:37:51 2020

@author: ls
"""

from __future__ import print_function

import threading
import time

from Src.GUI import gtk_gui_v2



# GTK
class GuiThread(threading.Thread):
    def __init__(self, tsampling=.2):

        threading.Thread.__init__(self)
        self.gui_win = gtk_gui_v2.GeckoBotCtrWin()


    def run(self):
        """ run the GUI """
        self.gui_win.run()

    def kill(self):
        self.gui_win.do_delete_event(None, force=True)

    def is_running(self):
        return self.gui_win.is_running


def main(wait=30):

    gui = GuiThread()
    gui.start()
    time.sleep(.03)
    print('GUI started .. ')

    try:
        while gui.is_running():
            time.sleep(.1)
    except KeyboardInterrupt:
        print('keyboard interrupt')
    finally:
        gui.kill()

    gui.join()
    print('all is done')


if __name__ == '__main__':

    main(wait=1)
