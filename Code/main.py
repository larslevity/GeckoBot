# -*- coding: utf-8 -*-
"""
Created on Sun May 29 13:51:21 2016

@author: ls

Prototyp for a main function
"""
from __future__ import print_function
import __builtin__

import sys
import threading
import time
from termcolor import colored

from Src.Visual.GUI import gtk_gui_v2
from Src.Management import datamanagement
from Src.Communication import client_commands as client
from Src.Management import exception
from Src.Management import state_machine


def print(*args, **kwargs):
    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


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


# MAIN
def main():
    """
    Main function of client:
    - init connection to the server(BBB)
    - init the graphical user interface(GUI)
    - start GUI
    - initialize a StateMachine for Communication with server
    - run the Communication StateMachine
        - switch between:
            - read_only (ask server for measurements and store them in GUI_Rec)
            - read_write (store measurements in GUIRec and write References
                from GUI_Task to the server)
            - change_state (Write a new State Request to the server)
        - terminate when GUI is closed
    - wait for GUI to join
    - close the socket - connection to server
    """
    TSAMPLING_GUI = .1
    START_STATE = 'PAUSE'

    print('Initialize connection ...')
    try:
        sock = client.init_BBB_connection('beaglebone')
        (sens_data, rec_u, rec_r, valve_data, dvalve_data, maxpressure,
         maxctrout, tsampling, PID_gains, pattern) = \
            client.get_meta_data(sock)
    except exception.TimeoutError:
        sock = None
        (sens_data, rec_u, rec_r, valve_data, dvalve_data, maxpressure,
         maxctrout, tsampling, PID_gains, pattern) = \
            ({'1': 0, '2': 0}, {'u1': 0, 'u2': 0},
             {'r1': 0, 'r2': 0}, ['1', '2', '3', '4', '5', '6'],
             ['1', '2', '3', '4'], .1, 1., .1,
             [[.1 for i in range(3)] for j in range(6)],
             [[0.1]*6+[False]*4+[3.0]]*2)

    print('Initialize GUI ...')
    print('with', len(valve_data), 'prop valves')
    print('with', len(dvalve_data), 'discrete valves')
    print('with', len(sens_data), 'pressure sensors')

    gui_rec = datamanagement.GUIRecorder()
    gui_task = datamanagement.GUITask(START_STATE, valve_data, dvalve_data,
                                      maxpressure, maxctrout, tsampling,
                                      PID_gains, pattern)
    gui_rec.append(sens_data)
    gui_rec.append(rec_u)
    gui_rec.append(rec_r)
    gui = GuiThread(gui_rec, gui_task)
    gui.start()

    print('Initialize Communication State Machine ...')
    automat = state_machine.StateMachine()
    automat.add_state('READ_ONLY', read_only)
    automat.add_state('READ_WRITE', read_write)
    automat.add_state('CHANGE_STATE', change_state)
    automat.add_state('EXIT', None, end_state=True)
    automat.set_start('READ_ONLY')
    cargo = Cargo(gui_rec, gui_task, sock, TSAMPLING_GUI)

    try:
        print('Run the StateMachine ...')
        automat.run(cargo)
    finally:
        print('Closing Socket ...')
        sock.close()

    gui.join()
    print('all is done')


def read_only(cargo):
    """
    Aslong as User did not send a change_state request:
        - ask server for actual measurements
        - store them in the GUI Recorder
        - send setting-request to server
    """
    current_state = cargo.gui_task.state
    while current_state == cargo.gui_task.state:
        sens_data, rec_u, rec_r = \
            client.update_sensors(cargo.sock, only_sens=False)
        cargo.gui_rec.append(sens_data)
        cargo.gui_rec.append(rec_u)
        cargo.gui_rec.append(rec_r)
        current_state = cargo.gui_task.state
        # set PID
        set_something(cargo)
        time.sleep(cargo.TSAMPLING_GUI)
    new_state = 'CHANGE_STATE'
    return (new_state, cargo)


def change_state(cargo):
    """
    - Send the change_state-request to server
    - decide which is the next state of the client-side communication
        statemachine
    """
    print('sending new state:', cargo.gui_task.state, 'to BBB ...')
    ans = client.change_state(cargo.sock, cargo.gui_task.state)
    print(ans)
    if ans == 'EXIT':
        new_state = 'EXIT'
    elif ans in ['USER_CONTROL', 'USER_REFERENCE']:
        new_state = 'READ_WRITE'
    else:
        new_state = 'READ_ONLY'
    return (new_state, cargo)


def read_write(cargo):
    """
    Aslong as User did not send a change_state request:
        - ask server for actual measurements
        - store them in the GUI Recorder
        - collect all tasks from GUITask
        - send them to server
    """
    current_state = cargo.gui_task.state

    print('gui_task.pwm:', cargo.gui_task.pwm)
    print('gui_task.dvalve_state:', cargo.gui_task.dvalve_state)

    while current_state == cargo.gui_task.state:
        # read
        sens_data, rec_u, rec_r = \
            client.update_sensors(cargo.sock, only_sens=False)
        cargo.gui_rec.append(sens_data)
        cargo.gui_rec.append(rec_u)
        cargo.gui_rec.append(rec_r)
        # write
        order = []
        if cargo.gui_task.state == 'USER_CONTROL':
            order = client.set_valve(valve_data=cargo.gui_task.pwm,
                                     order=order)
        elif cargo.gui_task.state == 'USER_REFERENCE':
            order = client.set_ref(ref_data=cargo.gui_task.ref, order=order)
        order = client.set_dvalve(cargo.gui_task.dvalve_state, order)
        client.send_all(cargo.sock, order)
        # meta
        current_state = cargo.gui_task.state
        # send settings
        set_something(cargo)
        # sleep
        time.sleep(cargo.TSAMPLING_GUI)
    new_state = 'CHANGE_STATE'
    return (new_state, cargo)


class Cargo(object):
    def __init__(self, rec, task, sock, TSAMPLING_GUI):
        """
        Container for client-sided Communication StateMachine
        *Initialize with:*

        Args:
            rec (datamanagement.GUIRecorder): Container of measurement history
            task (datamanagement.GUITask): Container of task buffer
            sock (socket.socket): Socket-Object for Communication
            TSAMPLING_GUI (float): Sampling Time of the GUI, which is also the
                sampling time of the communication statemachine
        """
        self.gui_rec = rec
        self.gui_task = task
        self.sock = sock
        self.TSAMPLING_GUI = TSAMPLING_GUI


def set_something(cargo):
    """
    call all available setting function:
        - PID Gains
        - Maximal Pressure
        - Max Controller Output
        - Sampling rate of the server
    """
    set_PID(cargo)
    set_maxpressure(cargo)
    set_maxctrout(cargo)
    set_tsampling(cargo)
    set_pattern(cargo)
    set_walking_state(cargo)


def set_PID(cargo):
    """
    If *set_gain* flag is set, this function send the according values of
    *GUITask* to the server.
    """
    for ctr_id, set_gain in enumerate(cargo.gui_task.set_PID):
        if set_gain:
            client.set_PID_gain(cargo.sock, ctr_id,
                                cargo.gui_task.PID_Params[ctr_id])
            cargo.gui_task.set_PID[ctr_id] = False


def set_maxpressure(cargo):
    """
    If *set_maxpressure* flag is set, this function send the according values
    of *GUITask* to the server.
    """
    if cargo.gui_task.set_maxpressure:
        client.set_maxpressure(cargo.sock, cargo.gui_task.maxpressure)
        cargo.gui_task.set_maxpressure = False


def set_maxctrout(cargo):
    """
    If *set_maxctrout* flag is set, this function send the according values
    of *GUITask* to the server.
    """
    if cargo.gui_task.set_maxctrout:
        client.set_maxctrout(cargo.sock, cargo.gui_task.maxctrout)
        cargo.gui_task.set_maxctrout = False


def set_tsampling(cargo):
    """
    If *set_tsampling* flag is set, this function send the according values
    of *GUITask* to the server.
    """
    if cargo.gui_task.set_tsampling:
        client.set_tsampling(cargo.sock, cargo.gui_task.tsampling)
        cargo.gui_task.set_tsampling = False


def set_pattern(cargo):
    if cargo.gui_task.set_pattern:
        client.set_pattern(cargo.sock, cargo.gui_task.pattern)
        cargo.gui_task.set_pattern = False


def set_walking_state(cargo):
    if cargo.gui_task.set_walking_state:
        client.set_walking_state(cargo.sock, cargo.gui_task.walking_state)
        cargo.gui_task.set_walking_state = False


if __name__ == '__main__':
    ARGS = sys.argv
    print('Argument List:', ARGS)

    main()
