#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 16:56:01 2019

@author: mustapha
"""

from __future__ import print_function

import threading
import time
import socket
import random
import numpy as np

from Src.Visual.GUI import gtk_gui_v2
from Src.Visual.GUI import datamanagement
from Src.Visual.GUI import save
from Src.Visual.PiCamera import pickler
from Src.Management import timeout
from Src.Management import exception


# GTK
class GuiThread(threading.Thread):
    def __init__(self, data):
        """
        Thread for the GUI provides:
        - visualization of
            - measurements
            - reference signals
            - actuator input signals
        *Initialize with:*
        Args:
            - data (datamanagement.GUIRecorder): Container of signal history
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


def main(wait=30):
    def fill_rnd_values():
        def gen_rnd_val(mul=1.):
            rnd = random.randint(0, 100)
            if rnd in range(30):
                return None
            return rnd/100.*mul

        pressure = {'p1': gen_rnd_val(), 'p2': gen_rnd_val()}
        rec_u = {'u1': gen_rnd_val(), 'u2': gen_rnd_val()}
        rec_r = {'r1': gen_rnd_val(), 'r2': gen_rnd_val(),
                 'x1': gen_rnd_val(300), 'y1': gen_rnd_val(300),
                 'x2': gen_rnd_val(300), 'y2': gen_rnd_val(300),
                 'x3': np.sin(time.time()/10.), 'y3': np.cos(time.time()/10.)}
        timestamp = {'time': time.time()}

        gui_rec.append(pressure)
        gui_rec.append(rec_u)
        gui_rec.append(rec_r)
        gui_rec.append(timestamp)

    def bind_to_client():
        server_socket = socket.socket()
        server_socket.bind(('', 12397))
        server_socket.listen(0)

        conn = server_socket.accept()[0]
        connection = conn.makefile('rb')
        return server_socket, conn, connection

    def recv_sample(connection):
        task_raw = connection.recv(4096)
        task = pickler.unpickle_data(task_raw)
        if task[0] == 'sample':
            send_back(connection, 'ACK')
            return task[1]
        elif task[0] == 'Exit':
            return 'Exit'
        else:
            return 0

    def send_back(connection, data_out):
        data_out_raw = pickler.pickle_data(data_out)
        connection.sendall(data_out_raw)

    gui_rec = datamanagement.GUIRecorder()

    print('wait for client .. ')
    is_client = False
    with timeout.timeout(wait):
        try:
            server_socket, conn, connection = bind_to_client()
            sample = recv_sample(conn)
            if sample:
                gui_rec.append(sample)
            is_client = True
            print("client DETECTED!")
        except exception.TimeoutError:
            print("There is no client. fill with rnd vals ...")
            fill_rnd_values()

    print('start GUI .. ')
    gui = GuiThread(gui_rec)
    gui.start()
    time.sleep(.5)
    print('GUI started .. ')

    try:
        while gui.is_running():
            if is_client:
                sample = recv_sample(conn)
                if sample and sample != 'Exit':
                    gui_rec.append(sample)
                elif sample == 'Exit':
                    gui.kill()
            else:
                fill_rnd_values()
            if gui_rec.record:
                save.save_last_sample_as_csv(gui_rec.recorded,
                                             gui_rec.record_filename)

            time.sleep(.03)
    except KeyboardInterrupt:
        print('keyboard interrupt')
    finally:
        connection.close()
        server_socket.close()
        gui.kill()

    gui.join()
    print('all is done')


if __name__ == '__main__':

    main(wait=30)
