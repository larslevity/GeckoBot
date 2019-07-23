# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 13:39:59 2019

@author: AmP
"""
import numpy as np
import errno
import logging
import time
import threading

from Src.Hardware import sensors as sensors
from Src.Hardware import actuators as actuators
from Src.Controller import controller as ctrlib
from Src.Management import state_machine
from Src.Math import IMUcalc


MAX_PRESSURE = 1.   # bar
MAX_CTROUT = 0.50     # [10V]
TSAMPLING = 0.001     # [sec]
PID = [1.05, 0.03, 0.01]    # [1]
PIDimu = [0.0117, 1.012, 0.31]

STARTSTATE = 'PAUSE'

logPath = "log/"
fileName = 'lowlevel_controller'
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


'''
Positions of IMUs:
<       ^       >
0 ----- 1 ----- 2
        |
        |
        |
3 ------4 ------5
<       v       >
In IMUcalc.calc_angle(acc0, acc1, rot_angle), "acc0" is turned by rot_angle
'''

IMUset = {
    0: {'id': 0},
    1: {'id': 1},
    2: {'id': 2},
    3: {'id': 3},
    4: {'id': 4},
    5: {'id': 5}
    }
CHANNELset = {
    0: {'PSensid': 4, 'pin': 'P9_22', 'ctr': PID, 'IMUs': [0, 1], 'IMUrot': -90, 'ctrIMU': PIDimu},
    1: {'PSensid': 5, 'pin': 'P8_19', 'ctr': PID, 'IMUs': [1, 2], 'IMUrot': -90, 'ctrIMU': PIDimu},
    2: {'PSensid': 2, 'pin': 'P9_21', 'ctr': PID, 'IMUs': [1, 4], 'IMUrot': 180, 'ctrIMU': PIDimu},
    3: {'PSensid': 3, 'pin': 'P8_13', 'ctr': PID, 'IMUs': [4, 1], 'IMUrot': 180, 'ctrIMU': PIDimu},
    4: {'PSensid': 0, 'pin': 'P9_14', 'ctr': PID, 'IMUs': [4, 3], 'IMUrot': -90, 'ctrIMU': PIDimu},
    5: {'PSensid': 1, 'pin': 'P9_16', 'ctr': PID, 'IMUs': [5, 4], 'IMUrot': -90, 'ctrIMU': PIDimu},
    6: {'PSensid': 7, 'pin': 'P9_28', 'ctr': PID, 'IMUs': [None], 'IMUrot': None, 'ctrIMU': None},
    7: {'PSensid': 6, 'pin': 'P9_42', 'ctr': PID, 'IMUs': [None], 'IMUrot': None, 'ctrIMU': None}
    }
DiscreteCHANNELset = {
    0: {'pin': 'P8_10'},
    1: {'pin': 'P8_7'},
    2: {'pin': 'P8_8'},
    3: {'pin': 'P8_9'}
    }


def init_channels():
    """
    Initialize the software representation of the hardware, i.e.
    Sensors, Proportional Valves, and Discrete Valves
    """

    # mplx address for IMU is 0x71

    imu_set = [imu for imu in IMUset]
    imu_used_ = [CHANNELset[name]['IMUs'] for name in CHANNELset]
    while [None] in imu_used_:
        imu_used_.remove([None])
    imu_used = list(np.unique([imu for subl in imu_used_ for imu in subl]))
    for imu in imu_used:
        if imu not in imu_set and imu is not None:
            raise KeyError(
                'IMU with name "{}"'.format(imu) + ' is used for angle' +
                'calculation, but is not in the set of connected IMUs')
    try:
        IMU = {}
        for name in IMUset:
            IMU[name] = sensors.MPU_9150(
                name=name, mplx_id=IMUset[name]['id'])
    except IOError:  # not connected
        IMU = False

    PSens, PValve, DValve, Controller, Imu_controller = {}, {}, {}, {}, {}
    for name in CHANNELset:
        PSens[name] = sensors.DPressureSens(
            name=name, mplx_id=CHANNELset[name]['PSensid'],
            maxpressure=MAX_PRESSURE)
        PValve[name] = actuators.Valve(
                name=name, pwm_pin=CHANNELset[name]['pin'])
        Controller[name] = ctrlib.PidController(
                CHANNELset[name]['ctr'], TSAMPLING, MAX_CTROUT)
        if CHANNELset[name]['IMUs'][-1]:
            Imu_controller[name] = ctrlib.PidController(
                CHANNELset[name]['ctrIMU'], TSAMPLING, MAX_CTROUT)

    for name in DiscreteCHANNELset:
        DValve[name] = actuators.DiscreteValve(
            name=name, pin=DiscreteCHANNELset[name]['pin'])

    return PSens, PValve, DValve, IMU, Controller, Imu_controller


class LowLevelController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.state = STARTSTATE
        self.sampling_time = TSAMPLING

        self.dvalve_ref = {name: 0. for name in DiscreteCHANNELset}
        self.pressure_ref = {name: 0. for name in CHANNELset}
        self.pwm_ref = {name: 20. for name in CHANNELset}

        self.rec_p = {name: 0.0 for name in CHANNELset}
        self.rec_aIMU = {name: None for name in IMUset}
        self.rec_u = {name: 0.0 for name in CHANNELset}

    def run(self):
        PSens, PValve, DValve, IMU, Ctr, ImuCtr = init_channels()

        def read_pressure_sens():
            for name in PSens:
                try:
                    self.rec_p[name] = PSens[name].get_value()
                except IOError as e:
                    if e.errno == errno.EREMOTEIO:
                        rootLogger.info(
                            'cant read pressure sensor.' +
                            ' Continue anyway ... Fail in [{}]'.format(name))
                    else:
                        rootLogger.exception('Sensor [{}]'.format(name))
                        rootLogger.error(e, exc_info=True)
                        raise e

        def read_imu():
            for name in IMU:
                try:
                    self.rec_aIMU[name] = IMU[name].get_acceleration()
                except IOError as e:
                    if e.errno == errno.EREMOTEIO:
                        rootLogger.exception(
                            'cant read imu device.' +
                            'Continue anyway ...Fail in [{}]'.format(name))
                    else:
                        rootLogger.exception('Sensor [{}]'.format(name))
                        rootLogger.error(e, exc_info=True)
                        raise e

        def set_dvalve():
            for name in DValve:
                state = self.dvalve_ref[name]
                DValve[name].set_state(state)

        def init_output():
            for name in PValve:
                PValve[name].set_pwm(20.)

        def pressure_check(pressure, pressuremax, cutoff):
            if pressure <= cutoff:
                out = 0
            elif pressure >= pressuremax:
                out = -MAX_CTROUT
            else:
                out = -MAX_CTROUT/(pressuremax-cutoff)*(pressure-cutoff)
            return out

        def cutoff(x, minx=-MAX_PRESSURE, maxx=MAX_PRESSURE):
            if x < minx:
                out = minx
            elif x > maxx:
                out = maxx
            else:
                out = x
            return out

        def angle_reference():
            rootLogger.info("Arriving in ANGLE_REFERENCE State. ")

            init_output()
            while self.state == 'ANGLE_REFERENCE':
                read_pressure_sens()
                if IMU:
                    set_dvalve()
                    read_imu()
                    imu_rec = self.rec_IMU
                    for name in ImuCtr:
                        ref = self.pressure_ref[name]*90.
                        idx0, idx1 = CHANNELset[name]['IMUs']
                        rot_angle = CHANNELset[name]['IMUrot']
                        acc0 = imu_rec[idx0]
                        acc1 = imu_rec[idx1]
                        sys_out = IMUcalc.calc_angle(acc0, acc1, rot_angle)
                        ctr_out = ImuCtr[name].output(ref, sys_out)
                        pressure = self.rec_p[name]
                        pressure_bound = pressure_check(
                                pressure, 1.5*MAX_PRESSURE, 1*MAX_PRESSURE)
                        ctr_out_ = cutoff(ctr_out+pressure_bound)
                        # for torso, set pwm to 0 if other ref is higher:
                        if name in [2, 3]:
                            other = 2 if name == 3 else 3
                            other_ref = self.pressure_ref[other]*90
                            if ref == 0 and ref == other_ref:
                                if pressure > .5:
                                    ctr_out_ = -MAX_CTROUT
                            elif (ref < other_ref or
                                  (ref == other_ref and ref > 0)):
                                ctr_out_ = -MAX_CTROUT
                        pwm = ctrlib.sys_input(ctr_out_)
                        PValve[name].set_pwm(pwm)
                        self.rec_u[name] = pwm
                        self.rec_aIMU[name] = round(sys_out, 2)

                time.sleep(self.sampling_time)
                new_state = self.state
            return (new_state)

        def feed_through():
            """
            Set the valves to the data recieved by the comm_tread
            """
            rootLogger.info("Arriving in FEED_THROUGH State: ")

            while self.state == 'FEED_THROUGH':
                # read
                read_pressure_sens()
                # write
                for name in PValve:
                    pwm = self.pwm_task[name]
                    PValve[name].set_pwm(pwm)
                    self.rec_u[name] = pwm
                set_dvalve()
                # meta
                time.sleep(self.sampling_time)
                new_state = self.state
            return (new_state)

        def pressure_reference():
            """
            Set the references for each valves to the data recieved by UI_tread
            """
            rootLogger.info("Arriving in PRESSURE_REFERENCE State: ")

            while self.state == 'PRESSURE_REFERENCE':
                # read
                read_pressure_sens()
                # write
                for name in PValve:
                    ref = self.pressure_ref[name]
                    sys_out = self.rec_p[name]
                    ctr_out = Ctr[name].output(ref, sys_out)
                    pwm = ctrlib.sys_input(ctr_out)
                    PValve[name].set_pwm(pwm)
                    self.rec_u[name] = pwm
                set_dvalve()
                # meta
                time.sleep(self.sampling_time)
                new_state = self.state
            return (new_state)

        def exit_cleaner():
            """ Clean everything up """
            rootLogger.info("cleaning ...")

            for name in PValve:
                PValve[name].set_pwm(0.)
            PValve[name].cleanup()
            for name in DValve:
                DValve[name].cleanup()

            return ('QUIT')

        def pause_state():
            """ do nothing. waiting for tasks """
            rootLogger.info("Arriving in PAUSE State: ")
            init_output()

            while self.state == 'PAUSE':
                read_pressure_sens()
                time.sleep(self.sampling_time)
                new_state = self.task_state_of_mainthread
            return (new_state)

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- RUN STATE MACHINE ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        rootLogger.info('Setting up the StateMachine ...')
        automat = state_machine.StateMachine()
        automat.add_state('PAUSE', pause_state)
        automat.add_state('ANGLE_REFERENCE', angle_reference)
        automat.add_state('FEED_THROUGH', feed_through)
        automat.add_state('PRESSURE_REFERENCE', pressure_reference)
        automat.add_state('EXIT', exit_cleaner)
        automat.add_state('QUIT', None, end_state=True)
        automat.set_start(STARTSTATE)

        try:
            rootLogger.info('Run the StateMachine ...')
            automat.run()
        except Exception as e:
            rootLogger.exception(e)
            rootLogger.error(e, exc_info=True)
            raise

    def kill(self):
        self.state = 'EXIT'

    def set_pressure_ref(self, ref):
        pass
    
    def set_dvalve_ref(self, ref):
        pass
    
    def set_pwm_ref(self, ref):
        pass
    
    def get_rec_p(self):
        pass
    
    def get_rec_u(self):
        pass
    
    def get_rec_aIMU(self):
        pass
