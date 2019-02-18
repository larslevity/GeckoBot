
""" Main function running on BBB """
from __future__ import print_function

import sys
import time
import logging
import errno
import numpy as np
from socket import error as SocketError

from Src.Hardware import sensors as sensors
from Src.Hardware import actuators as actuators
from Src.Management import state_machine
from Src.Management import timeout
from Src.Management import exception
from Src.Communication import user_interface as HUI
from Src.Math import IMUcalc
from Src.Controller import controller as ctrlib
from Src.Visual.PiCamera import client
from Src.Management import load_pattern as ptrn


logPath = "log/"
fileName = 'testlog'
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


# ------------ CAMERA INIT

def init_server_connections(IMGPROC=False):
    camerasock, imgprocsock, plotsock = None, None, None
    RPi_ip = '134.28.136.49'
    pc_ip = '134.28.136.131'

    # RPi connection
    with timeout.timeout(12):
        try:
            rootLogger.info("Try to start server ...")
            if IMGPROC:
                client.start_img_processing(RPi_ip)
                time.sleep(10)
                imgprocsock = client.IMGProcSocket(RPi_ip)
                rootLogger.info("RPi Server found: Img Processing is running")
            else:
                client.start_server(RPi_ip)
                time.sleep(3)
                camerasock = client.ClientSocket(RPi_ip)
                rootLogger.info("RPi Server found: MakeImageServer is running")
        except exception.TimeoutError:
            rootLogger.info("Server not found")
        except SocketError as err:
            if err.errno == errno.ECONNREFUSED:
                rootLogger.info("RPi Server refused connection")
            elif err.errno == errno.EADDRINUSE:
                rootLogger.info("RPi Server already in Use")
            else:
                raise
    # PC Dell Latitude Connection
    with timeout.timeout(2):
        try:
            plotsock = client.LivePlotterSocket(pc_ip)
            rootLogger.info("Connected to LivePlot Server")
        except exception.TimeoutError:
            rootLogger.info("Live Plot Server not found")
        except SocketError as err:
            if err.errno == errno.ECONNREFUSED:
                rootLogger.info("LivePlotter Server refused connection")
            elif err.errno == errno.EADDRINUSE:
                rootLogger.info("LivePlotter Server already in Use")
            else:
                raise

    return camerasock, imgprocsock, plotsock


# ------------ PATTERN INIT

MAX_PRESSURE = 1.   # bar
MAX_CTROUT = 0.50     # [10V]
TSAMPLING = 0.001     # [sec]
PID = [1.05, 0.03, 0.01]    # [1]
PIDimu = [0.0117, 1.012, 0.31]

START_STATE = 'PAUSE'
PRINTSTATE = False


# ------------ CHANNELS INIT

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
    rootLogger.info("Initialize IMUs ...")
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
    rootLogger.info("IMU detected?: {}".format(not(not(IMU))))

    rootLogger.info("Initialize Channels ...")
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


def main():
    """
    - Run the State Machine
        - switch between following states according to user or system given
          conditions:
            - PAUSE (do nothing but read sensors)
            - FEED_THROUGH (Set PWM direct from User Interface)
            - PRESSURE_REFERENCE (Use PSensCtr to track user-given reference)
            - ANGLE_REFERENCE (Use IMUCtr to track user-given reference)
            - EXIT (Cleaning..)
    - wait for communication thread to join
    """
    class SharedMemory(object):
        """ Data, which is shared between Threads """
        def __init__(self):
            self.task_state_of_mainthread = START_STATE
            self.actual_state_of_mainthread = START_STATE
            self.sampling_time = TSAMPLING

            self.dvalve_task = {name: 0. for name in DiscreteCHANNELset}
            self.ref_task = {name: 0. for name in CHANNELset}
            self.pwm_task = {name: 20. for name in CHANNELset}

            self.rec = {name: 0.0 for name in CHANNELset}
            self.rec_IMU = {name: None for name in IMUset}
            self.rec_u = {name: 0.0 for name in CHANNELset}
            self.rec_angle = {name: None for name in CHANNELset}

            self.ptrndic = {
                name: ptrn.read_list_from_csv('Patterns/'+name)
                for name in ptrn.get_csv_files()}
            self.ptrndic['selected'] = sorted(list(self.ptrndic.keys()))[0]
            self.pattern = self.ptrndic[self.ptrndic['selected']]

    rootLogger.info('Initialize Hardware ...')
    PSens, PValve, DValve, IMU, Ctr, ImuCtr = init_channels()

    rootLogger.info('Initialize the shared variables, i.e. cargo ...')
    shared_memory = SharedMemory()


    """ ---------------- Sensor  Evaluation ------------------------- """
    def read_sens(shared_memory):
        for name in PSens:
            try:
                shared_memory.rec[name] = PSens[name].get_value()
            except IOError as e:
                if e.errno == errno.EREMOTEIO:
                    rootLogger.info(
                        'cant read pressure sensor.' +
                        ' Continue anyway ... Fail in [{}]'.format(name))
                else:
                    rootLogger.exception('Sensor [{}]'.format(name))
                    rootLogger.error(e, exc_info=True)
                    raise e
        return shared_memory

    def read_imu(shared_memory):
        for name in IMU:
            try:
                shared_memory.rec_IMU[name] = IMU[name].get_acceleration()
            except IOError as e:
                if e.errno == errno.EREMOTEIO:
                    rootLogger.exception(
                        'cant read imu device.' +
                        'Continue anyway ...Fail in [{}]'.format(name))
                else:
                    rootLogger.exception('Sensor [{}]'.format(name))
                    rootLogger.error(e, exc_info=True)
                    raise e
        return shared_memory

    """ ---------------- HELP FUNCTIONS ------------------------- """

    def set_dvalve():
        for name in DValve:
            state = shared_memory.dvalve_task[name]
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

    """ ---------------- ----- ------- ------------------------- """
    """ ---------------- State Handler ------------------------- """
    """ ---------------- ----- ------- ------------------------- """

    def angle_reference(shared_memory):
        rootLogger.info("Arriving in ANGLE_REFERENCE State. ")
        shared_memory.actual_state_of_mainthread = 'ANGLE_REFERENCE'

        init_output()
        while shared_memory.task_state_of_mainthread == 'ANGLE_REFERENCE':
            shared_memory = read_sens(shared_memory)
            if IMU:
                set_dvalve()
                shared_memory = read_imu(shared_memory)
                imu_rec = shared_memory.rec_IMU
                for name in ImuCtr:
                    ref = shared_memory.ref_task[name]*90.
                    idx0, idx1 = CHANNELset[name]['IMUs']
                    rot_angle = CHANNELset[name]['IMUrot']
                    acc0 = imu_rec[idx0]
                    acc1 = imu_rec[idx1]
                    sys_out = IMUcalc.calc_angle(acc0, acc1, rot_angle)
                    ctr_out = ImuCtr[name].output(ref, sys_out)
                    pressure = shared_memory.rec[name]
                    pressure_bound = pressure_check(
                            pressure, 1.5*MAX_PRESSURE, 1*MAX_PRESSURE)
                    ctr_out_ = cutoff(ctr_out+pressure_bound)
                    # for torso, set pwm to 0 if other ref is higher:
                    if name in [2, 3]:
                        other = 2 if name == 3 else 3
                        other_ref = shared_memory.ref_task[other]*90
                        if ref == 0 and ref == other_ref:
                            if pressure > .5:
                                ctr_out_ = -MAX_CTROUT
                        elif ref < other_ref or (ref == other_ref and ref > 0):
                            ctr_out_ = -MAX_CTROUT
                    pwm = ctrlib.sys_input(ctr_out_)
                    PValve[name].set_pwm(pwm)
                    shared_memory.rec_u[name] = pwm
                    shared_memory.rec_angle[name] = round(sys_out, 2)

            time.sleep(shared_memory.sampling_time)
            new_state = shared_memory.task_state_of_mainthread
        return (new_state, shared_memory)

    def feed_through(shared_memory):
        """
        Set the valves to the data recieved by the comm_tread
        """
        rootLogger.info("Arriving in FEED_THROUGH State: ")
        shared_memory.actual_state_of_mainthread = 'FEED_THROUGH'

        while shared_memory.task_state_of_mainthread == 'FEED_THROUGH':
            # read
            shared_memory = read_sens(shared_memory)
            # write
            for name in PValve:
                pwm = shared_memory.pwm_task[name]
                PValve[name].set_pwm(pwm)
                shared_memory.rec_u[name] = pwm
            set_dvalve()
            # meta
            time.sleep(shared_memory.sampling_time)
            new_state = shared_memory.task_state_of_mainthread
        return (new_state, shared_memory)

    def pressure_reference(shared_memory):
        """
        Set the references for each valves to the data recieved by the UI_tread
        """
        rootLogger.info("Arriving in PRESSURE_REFERENCE State: ")
        shared_memory.actual_state_of_mainthread = 'PRESSURE_REFERENCE'

        while shared_memory.task_state_of_mainthread == 'PRESSURE_REFERENCE':
            # read
            shared_memory = read_sens(shared_memory)
            # write
            for name in PValve:
                ref = shared_memory.ref_task[name]
                sys_out = shared_memory.rec[name]
                ctr_out = Ctr[name].output(ref, sys_out)
                pwm = ctrlib.sys_input(ctr_out)
                PValve[name].set_pwm(pwm)
                shared_memory.rec_u[name] = pwm
            set_dvalve()
            # meta
            time.sleep(shared_memory.sampling_time)
            new_state = shared_memory.task_state_of_mainthread
        return (new_state, shared_memory)

    def exit_cleaner(shared_memory):
        """ Clean everything up """
        rootLogger.info("cleaning ...")
        shared_memory.actual_state_of_mainthread = 'EXIT'
        shared_memory.task_state_of_mainthread = 'EXIT'

        for name in PValve:
            PValve[name].set_pwm(0.)
        PValve[name].cleanup()
        for name in DValve:
            DValve[name].cleanup()

        return ('QUIT', shared_memory)

    def pause_state(shared_memory):
        """ do nothing. waiting for tasks """
        rootLogger.info("Arriving in PAUSE State: ")
        shared_memory.actual_state_of_mainthread = 'PAUSE'
        init_output()

        while shared_memory.task_state_of_mainthread == 'PAUSE':
            shared_memory = read_sens(shared_memory)
            time.sleep(shared_memory.sampling_time)
            new_state = shared_memory.task_state_of_mainthread
        return (new_state, shared_memory)

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
    automat.set_start(START_STATE)

    rootLogger.info('Starting Communication Thread ...')
    communication_thread = HUI.HUIThread(shared_memory, rootLogger)
    communication_thread.setDaemon(True)
    communication_thread.start()
    rootLogger.info('started UI Thread as daemon?: {}'.format(
            communication_thread.isDaemon()))

    camerasock, imgprocsock, plotsock = init_server_connections()
    communication_thread.set_camera_socket(camerasock)

    if PRINTSTATE:
        printer_thread = HUI.Printer(shared_memory, imgprocsock, plotsock, IMU)
        printer_thread.setDaemon(True)
        printer_thread.start()
        rootLogger.info('Started the Printer Thread')
    

    try:
        rootLogger.info('Run the StateMachine ...')
        automat.run(shared_memory)
    except KeyboardInterrupt:
        rootLogger.exception('keyboard interrupt detected...   killing UI')
       
    except Exception as err:
        rootLogger.exception(
            '\n----------caught exception! in Main Thread----------------\n')
        rootLogger.exception("Unexpected error:\n", sys.exc_info()[0])
        rootLogger.exception(sys.exc_info()[1])
        rootLogger.error(err, exc_info=True)
        rootLogger.info('\n ----------------------- killing UI --')
    finally:
        if PRINTSTATE:
            printer_thread.kill()
        if imgprocsock:
            imgprocsock.close()
        if camerasock:
            camerasock.close()
        if plotsock:
            plotsock.close()
        communication_thread.kill()
        
    communication_thread.join()
    if PRINTSTATE:
        printer_thread.join()
    rootLogger.info('All is done ...')
    sys.exit(0)


if __name__ == '__main__':
    main()
