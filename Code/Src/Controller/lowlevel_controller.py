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

from Src.Management.thread_communication import llc_ref
from Src.Management.thread_communication import llc_rec


from Src.Hardware.configuration import CHANNELset
from Src.Hardware.configuration import DiscreteCHANNELset
from Src.Hardware.configuration import IMUset
from Src.Hardware.configuration import MAX_CTROUT
from Src.Hardware.configuration import TSAMPLING


rootLogger = logging.getLogger()
n_pc = len(llc_ref.pressure)


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

    DValve, PValve, Imu_controller = {}, {}, {}
    for name in CHANNELset:
        PValve[name] = actuators.Valve(
                name=name, pwm_pin=CHANNELset[name]['pin'])
        if CHANNELset[name]['IMUs'][-1]:
            Imu_controller[name] = ctrlib.PidController(
                CHANNELset[name]['ctr'], TSAMPLING, MAX_CTROUT)

    for name in DiscreteCHANNELset:
        DValve[name] = actuators.DiscreteValve(
            name=name, pin=DiscreteCHANNELset[name]['pin'])

    return PValve, DValve, IMU, Imu_controller


class LowLevelController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sampling_time = TSAMPLING
        self.imu_in_use = None

    def is_imu_in_use(self):
        return self.imu_in_use

    def run(self):
        PValve, DValve, IMU, ImuCtr = init_channels()
        if IMU:
            self.imu_in_use = True
        else:
            self.imu_in_use = False

        def read_imu():
            for name in IMU:
                try:
                    llc_rec.aIMU[name] = IMU[name].get_acceleration()
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
                state = llc_ref.dvalve[name]
                DValve[name].set_state(state)

        def init_output():
            for name in PValve:
                PValve[name].set_pwm(0.)

        def angle_reference():
            rootLogger.info("Arriving in ANGLE_REFERENCE State. ")

            init_output()
            while llc_ref.state == 'ANGLE_REFERENCE':
                if IMU:
                    set_dvalve()
                    read_imu()
                    imu_rec = self.IMU
                    for name in ImuCtr:
                        ref = llc_ref.alpha[name]
                        idx0, idx1 = CHANNELset[name]['IMUs']
                        rot_angle = CHANNELset[name]['IMUrot']
                        acc0 = imu_rec[idx0]
                        acc1 = imu_rec[idx1]
                        sys_out = IMUcalc.calc_angle(acc0, acc1, rot_angle)
                        pressure_ref = ImuCtr[name].output(ref, sys_out)

                        # for torso, set pressure to 0 if other ref is higher:
                        if name in [2, 3]:
                            other = 2 if name == 3 else 3
                            other_ref = llc_ref.pressure[other]
                            if ref == 0 and other_ref == 0:
                                if pressure_ref > .2:
                                    pressure_ref = 0
                            elif (ref < other_ref or
                                  (ref == other_ref and ref > 0)):
                                pressure_ref = 0
                        pwm = ctrlib.sys_input(pressure_ref)
                        PValve[name].set_pwm(pwm)
                        llc_ref.pressure[name] = pressure_ref
                        llc_rec.u[name] = pwm
                        llc_rec.aIMU[name] = round(sys_out, 2)

                time.sleep(self.sampling_time)

            return llc_ref.state

        def pressure_reference():
            rootLogger.info("Arriving in PRESSURE_REFERENCE State: ")
            llc_ref.alpha = {idx: None for idx in range(n_pc)}
            while llc_ref.state == 'PRESSURE_REFERENCE':
                # write
                for name in PValve:
                    pressure_ref = llc_ref.pressure[name]
                    pwm = ctrlib.sys_input(pressure_ref)
                    PValve[name].set_pwm(pwm)
                    llc_rec.u[name] = pwm
                set_dvalve()
                # meta
                time.sleep(self.sampling_time)

            return llc_ref.state

        def exit_cleaner():
            """ Clean everything up """
            rootLogger.info("cleaning Output Pins ...")

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

            while llc_ref.state == 'PAUSE':
                time.sleep(self.sampling_time)

            return llc_ref.state

        """ ---------------- ----- ------- ----------------------------- """
        """ ---------------- RUN STATE MACHINE ------------------------- """
        """ ---------------- ----- ------- ----------------------------- """

        automat = state_machine.StateMachine()
        automat.add_state('PAUSE', pause_state)
        automat.add_state('ANGLE_REFERENCE', angle_reference)
        automat.add_state('PRESSURE_REFERENCE', pressure_reference)
        automat.add_state('EXIT', exit_cleaner)
        automat.add_state('QUIT', None, end_state=True)
        automat.set_start('PAUSE')

        try:
            rootLogger.info('Run LowLevelCtr ...')
            automat.run()
        except Exception as e:
            rootLogger.exception(e)
            rootLogger.error(e, exc_info=True)
            raise
        rootLogger.info('LowLevelCtr is done ...')

    def kill(self):
        llc_ref.state = 'EXIT'
