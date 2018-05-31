# pylint: disable = invalid-name, no-member, fixme
""" Main function running on BBB
According to: https://pymotw.com/2/socket/tcp.html

---------------------------
In order to enable 'P9_28' as pwm pin, you have to load 'cape-universala' in
/boot/uEnv.txt by adding following line:

nano /boot/uEnv.txt: 
cape_enable=bone_capemgr.enable_partno=cape-universala

and then configure it with:

root@beaglebone:# config-pin P9_28 pwm
---------------------------
In order to autorun this script after booting the BBB use crontab like this:
root@beaglebone:# crontab -e -u root

adding the following lines to the cron boot jobs:

@reboot config-pin P9_28 pwm
@reboot python /home/debian/Git/GeckoBot/Code/server_hardware_controlled.py &

NOTE: Dont forget the '&' at the end. Otherwise it will block the console.
And you wont be able to ssh into it.
But with the '&' it will run as background process and will be able to ssh into
the BBB.

Ending Background Processes

Since the python script will run in the background, we need to find it and
end it manually. Enter this to find the processing running off the file we
wrote earlier.

ps aux | grep home/debian/GeckoBot/Code/server_hardware_controlled.py

You will get something like this:
    root    873     0.1     0.6     7260    3264    ?   S   22:19   0:01 python home/debian/GeckoBot/Code/server_hardware_controlled.py

The number 873 is the process ID. Then, just use the process ID and kill
the process.

root@beaglebone:# kill 873


Ref:
https://billwaa.wordpress.com/2014/10/03/beaglebone-black-launch-python-script-at-boot-like-arduino-sketch/
---------------------------

Okay, cron gives error:
try with daemontools - Ref:
http://samliu.github.io/2017/01/10/daemontools-cheatsheet.html

---------------------------


"""
from __future__ import print_function

import sys
#import traceback
import time
import logging

from Src.Hardware import sensors as sensors
from Src.Hardware import actuators as actuators
from Src.Management import state_machine
from Src.Communication import hardware_control as HUI

from Src.Controller import walk_commander
from Src.Controller import controller as ctrlib


logPath = "log/"
fileName = 'testlog'

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)


fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


# MAX_PRESSURE = 0.85    # [bar] v2.2
# MAX_PRESSURE = 0.93    # [bar] v2.3
MAX_PRESSURE = 0.85    # [bar] v2.4
MAX_CTROUT = 0.50     # [10V]
TSAMPLING = 0.001     # [sec]
PID = [1.05, 0.03, 0.01]    # [1]

## v2.2
#PATTERN = [[0.0, 0.8, 0.9, 0.0, 0.25, 0.8, False, True, True, False, 5.0],
#           [0.0, 0.8, 0.9, 0.0, 0.25, 0.8, True, True, True, True, 2.0],
#           [0.0, 0.8, 0.9, 0.0, 0.25, 0.8, True, False, False, True, 1.0],
#           [0.8, 0.0, 0.0, 0.99, 0.8, 0.3, True, False, False, True, 5.0],
#           [0.8, 0.0, 0.0, 0.99, 0.8, 0.3, True, True, True, True, 2.0],
#           [0.8, 0.0, 0.0, 0.99, 0.8, 0.3, False, True, True, False, 1.0]]

## v2.3
#PATTERN = [[0.0, 0.74, 0.99, 0.0, 0.25, 0.63, False, True, True, False, 5.0],
#           [0.0, 0.74, 0.99, 0.0, 0.25, 0.63, True, True, True, True, 2.0],
#           [0.0, 0.74, 0.99, 0.0, 0.25, 0.63, True, False, False, True, 1.0],
#           [0.72, 0.0, 0.0, 0.99, 0.69, 0.25, True, False, False, True, 5.0],
#           [0.72, 0.0, 0.0, 0.99, 0.69, 0.25, True, True, True, True, 2.0],
#           [0.72, 0.0, 0.0, 0.99, 0.69, 0.25, False, True, True, False, 1.0]]

## v2.4
#PATTERN = [[0.0, 0.79, 0.99, 0.0, 0.25, 0.78, False, True, True, False, 5.0],
#           [0.0, 0.79, 0.99, 0.0, 0.25, 0.78, True, True, True, True, 2.0],
#           [0.0, 0.79, 0.99, 0.0, 0.25, 0.78, True, False, False, True, 1.0],
#           [0.64, 0.0, 0.0, 0.99, 0.75, 0.3, True, False, False, True, 5.0],
#           [0.64, 0.0, 0.0, 0.99, 0.75, 0.3, True, True, True, True, 2.0],
#           [0.64, 0.0, 0.0, 0.99, 0.75, 0.3, False, True, True, False, 1.0]]

## v2.5
#PATTERN = [[0.0, 0.68, 0.93, 0.0, 0.30, 0.74, False, True, True, False, 5.0],
#           [0.0, 0.68, 0.93, 0.0, 0.30, 0.74, True, True, True, True, 2.0],
#           [0.0, 0.68, 0.93, 0.0, 0.30, 0.74, True, False, False, True, 1.0],
#           [0.92, 0.0, 0.0, 0.92, 0.90, 0.25, True, False, False, True, 5.0],
#           [0.92, 0.0, 0.0, 0.92, 0.90, 0.25, True, True, True, True, 2.0],
#           [0.92, 0.0, 0.0, 0.92, 0.90, 0.25, False, True, True, False, 1.0]]

## v2.6
#PATTERN = [[0.0, 0.99, 0.97, 0.0, 0.25, 0.71, False, True, True, False, 5.0],
#           [0.0, 0.99, 0.97, 0.0, 0.25, 0.71, True, True, True, True, 2.0],
#           [0.0, 0.99, 0.97, 0.0, 0.25, 0.71, True, False, False, True, 1.0],
#           [0.77, 0.0, 0.0, 0.93, 0.70, 0.25, True, False, False, True, 5.0],
#           [0.77, 0.0, 0.0, 0.93, 0.70, 0.25, True, True, True, True, 2.0],
#           [0.77, 0.0, 0.0, 0.93, 0.70, 0.25, False, True, True, False, 1.0]]



PATTERN30_00 = [[0.25, 0.66, 0.99, 0.0, 0.25, 0.86, 0.0, .0, False, True, True, False, 2.0],
                [0.0, 0.66, 0.99, 0.0, 0.25, 0.86, 0.0, .0, True, True, True, True, .66],
                [0.0, 0.66, 0.99, 0.0, 0.25, 0.86, 0.0, .0, True, False, False, True, 0.25],
                [0.74, 0.25, 0.0, 0.85, 0.65, 0.25, 0.0, .0, True, False, False, True, 2.0],
                [0.74, 0.0, 0.0, 0.85, 0.65, 0.25, 0.0, .0, True, True, True, True, .66],
                [0.74, 0.0, 0.0, 0.85, 0.65, 0.25, 0.0, .0, False, True, True, False, 0.25]]

#
#PATTERN30_20 = [[0.25, 0.66, 0.99, 0.0, 0.25, 0.80, False, True, True, False, 3.0],
#                [0.0, 0.66, 0.99, 0.0, 0.25, 0.80, True, True, True, True, 1.0],
#                [0.0, 0.66, 0.99, 0.0, 0.25, 0.80, True, False, False, True, 0.5],
#                [0.74, 0.25, 0.0, 0.85, 0.65, 0.25, True, False, False, True, 3.0],
#                [0.74, 0.0, 0.0, 0.85, 0.65, 0.25, True, True, True, True, 1.0],
#                [0.74, 0.0, 0.0, 0.85, 0.65, 0.25, False, True, True, False, 0.5]]
#
## v3.0
#PATTERN30_50 = [[0.2, 0.62, 0.99, 0.0, 0.2, 0.71, False, True, True, False, 3.0],
#                [0.0, 0.62, 0.99, 0.0, 0.2, 0.71, True, True, True, True, 1.0],
#                [0.0, 0.62, 0.99, 0.0, 0.2, 0.71, True, False, False, True, 0.5],
#                [0.63, 0.25, 0.0, 0.9, 0.52, 0.2, True, False, False, True, 3.0],
#                [0.63, 0.0, 0.0, 0.9, 0.52, 0.2, True, True, True, True, 1.0],
#                [0.63, 0.0, 0.0, 0.9, 0.52, 0.2, False, True, True, False, 0.5]]
#MAX_PRESSURE50_50 = 0.95    # [bar] v2.4


# v3.0
PATTERN = PATTERN30_00

INITIAL_PATTERN = [PATTERN[-1][:8] + [False, False, False, False, 3.0],
                   PATTERN[-1][:8] + [False, True, True, False, 1.0]]

FINAL_PATTERN = [PATTERN[-1][:8] + [False, True, True, False, 5.0],
                 [0.]*8 + [False]*4 + [.5]]


def init_hardware():
    """
    Initialize the software representation of the hardware, i.e.
    Sensors, Proportional Valves, and Discrete Valves

    The connected Pins are hardcoded here!

    Return:
        (list of sensors.DPressureSens): list of software repr of initialized
            Sensors
        (list of actuators.Valve): list of software repr of initialized
            proportional valves
        (list of actuators.DValve): list of software repr of initialized
            discrete valves
    """
    rootLogger.info("Initialize Sensors ...")
    sens = []
    sets = [{'name': '0', 'id': 4},
            {'name': '1', 'id': 5},
            {'name': '2', 'id': 2},
            {'name': '3', 'id': 3},
            {'name': '4', 'id': 0},
            {'name': '5', 'id': 1},
            {'name': '6', 'id': 7},
            {'name': '7', 'id': 6}]
    for s in sets:
        sens.append(sensors.DPressureSens(name=s['name'], mplx_id=s['id'],
                                          maxpressure=MAX_PRESSURE))

    rootLogger.info('Initialize Valves ...')
    valve = []
    sets = [{'name': '0', 'pin': 'P9_22'},     # Upper Left Leg
            {'name': '1', 'pin': 'P8_19'},     # Upper Right Leg
            {'name': '2', 'pin': 'P9_21'},     # Left Belly
            {'name': '3', 'pin': 'P8_13'},     # Right Belly
            {'name': '4', 'pin': 'P9_14'},     # Lower Left Leg
            {'name': '5', 'pin': 'P9_16'},     # Lower Right Leg
            {'name': '6', 'pin': 'P9_28'},
            {'name': '7', 'pin': 'P9_42'}]
    for elem in sets:
        valve.append(actuators.Valve(name=elem['name'], pwm_pin=elem['pin']))

    dvalve = []
    dsets = [{'name': '0', 'pin': 'P8_10'},      # Upper Left Leg
             {'name': '1', 'pin': 'P8_7'},     # Upper Right Leg
             {'name': '2', 'pin': 'P8_8'},     # Lower Left Leg
             {'name': '3', 'pin': 'P8_9'}]     # Lower Right Leg]
    for elem in dsets:
        dvalve.append(actuators.DiscreteValve(
            name=elem['name'], pin=elem['pin']))

    return sens, valve, dvalve


def init_controller():
    """
    Initialize the set of controllers. At moment only PID Controller are
    implemented.

    If you want to use other controllers, just construct a class
    that inherits from the abstract Class controller.controller. Then you are
    forced to use the supported interface.

    The default gainz (P, I and D) are hardcoded at the beginning of
    *server.py*, but can easily be changed via the user interface of the
    client.

    Return:
        (list of controller.PIDController)
    """
    tsamplingPID = TSAMPLING
    maxoutPID = MAX_CTROUT
    controller = []
    sets = [{'name': '0', 'P': PID[0], 'I': PID[1], 'D': PID[2]},
            {'name': '1', 'P': PID[0], 'I': PID[1], 'D': PID[2]},
            {'name': '2', 'P': PID[0], 'I': PID[1], 'D': PID[2]},
            {'name': '3', 'P': PID[0], 'I': PID[1], 'D': PID[2]},
            {'name': '4', 'P': PID[0], 'I': PID[1], 'D': PID[2]},
            {'name': '5', 'P': PID[0], 'I': PID[1], 'D': PID[2]},
            {'name': '6', 'P': PID[0], 'I': PID[1], 'D': PID[2]},
            {'name': '7', 'P': PID[0], 'I': PID[1], 'D': PID[2]}]
    for elem in sets:
        controller.append(
            ctrlib.PidController([elem['P'], elem['I'], elem['D']],
                                 tsamplingPID, maxoutPID))
    return controller


def main():
    """
    main Function of server side:
    - init software repr of the hardware
    - init controllers
    - init the Container which contains all shared variables, i.e. Cargo
    - init the server-side StateMachine
    - init the server-side Communication Thread
    - start the Communication Thread
    - Run the State Machine
        - switch between following states according to user or system given
          conditions:
            - PAUSE (do nothing but read sensors)
            - ERROR (Print Error Message)
            - REFERENCE_TRACKING (start the controller.WalkingCommander)
            - USER_CONTROL (Set PWM direct from User Interface)
            - USER_REFERENCE (Use controller to track user-given reference)
            - EXIT (Cleaning..)
    - wait for communication thread to join
    - fin
    """
    rootLogger.info('Initialize Hardware ...')
    sens, valve, dvalve = init_hardware()
    controller = init_controller()

    rootLogger.info('Initialize the shared variables, i.e. cargo ...')
    start_state = 'PAUSE'
    cargo = Cargo(start_state, sens=sens,
                  valve=valve, dvalve=dvalve, controller=controller)

    rootLogger.info('Setting up the StateMachine ...')
    automat = state_machine.StateMachine()
    automat.add_state('PAUSE', pause_state)
    automat.add_state('ERROR', error_state)
    automat.add_state('REFERENCE_TRACKING', reference_tracking)
    automat.add_state('USER_CONTROL', user_control)
    automat.add_state('USER_REFERENCE', user_reference)
    automat.add_state('EXIT', exit_cleaner)
    automat.add_state('QUIT', None, end_state=True)
    automat.set_start(start_state)

    rootLogger.info('Starting Communication Thread ...')
    communication_thread = HUI.HUIThread(cargo, rootLogger)
    communication_thread.setDaemon(True)
    communication_thread.start()
    rootLogger.info('started UI Thread as daemon?: {}'.format(
            communication_thread.isDaemon()))

    try:
        rootLogger.info('Run the StateMachine ...')
        automat.run(cargo)
    # pylint: disable = bare-except
    except KeyboardInterrupt:
        rootLogger.exception('keyboard interrupt detected...   killing UI')
        communication_thread.kill()
    except IOError:
        rootLogger.exception('cant read i2c device. Continue anyway ...')
    except Exception as err:
        rootLogger.exception('\n----------caught exception! in Main Thread----------------\n')
        rootLogger.exception("Unexpected error:\n", sys.exc_info()[0])
        rootLogger.exception(sys.exc_info()[1])
        rootLogger.error(err, exc_info=True)
#        traceback.print_tb(sys.exc_info()[2])

        rootLogger.info('\n ----------------------- killing UI --')
        communication_thread.kill()

    communication_thread.join()
    rootLogger.info('All is done ...')
    sys.exit(0)


#  SET UP the state Handler
def pause_state(cargo):
    """
    do nothing. waiting for tasks
    """
    rootLogger.info("Arriving in PAUSE State: ")
    cargo.actual_state = 'PAUSE'

    for valve in cargo.valve:
        valve.set_pwm(1.)
        cargo.rec_u['u{}'.format(valve.name)] = 0.
        cargo.rec_r['r{}'.format(valve.name)] = None

    while cargo.state == 'PAUSE':
        for sensor in cargo.sens:
            cargo.rec[sensor.name] = sensor.get_value()
        time.sleep(cargo.sampling_time)
        new_state = cargo.state
    return (new_state, cargo)


def user_control(cargo):
    """
    Set the valves to the data recieved by the comm_tread
    """
    rootLogger.info("Arriving in USER_CONTROL State: ")
    cargo.actual_state = 'USER_CONTROL'

    while cargo.state == 'USER_CONTROL':
        # read
        for sensor in cargo.sens:
            cargo.rec[sensor.name] = sensor.get_value()

        # write
        for valve in cargo.valve:
            pwm = cargo.pwm_task[valve.name]
            valve.set_pwm(pwm)
            cargo.rec_r['r{}'.format(valve.name)] = None
            cargo.rec_u['u{}'.format(valve.name)] = pwm/100.

        for dvalve in cargo.dvalve:
            state = cargo.dvalve_task[dvalve.name]
            dvalve.set_state(state)

        # meta
        time.sleep(cargo.sampling_time)

        new_state = cargo.state
    return (new_state, cargo)


def user_reference(cargo):
    """
    Set the references for each valves to the data recieved by the comm_tread
    """
    rootLogger.info("Arriving in USER_REFERENCE State: ")
    cargo.actual_state = 'USER_REFERENCE'

    while cargo.state == 'USER_REFERENCE':
        # read
        for sensor in cargo.sens:
            cargo.rec[sensor.name] = sensor.get_value()

        # write
        for valve, controller in zip(cargo.valve, cargo.controller):
            ref = cargo.ref_task[valve.name]
            sys_out = cargo.rec[valve.name]
            ctr_out = controller.output(ref, sys_out)
            valve.set_pwm(ctrlib.sys_input(ctr_out))
            cargo.rec_r['r{}'.format(valve.name)] = ref
            cargo.rec_u['u{}'.format(valve.name)] = ctr_out

        for dvalve in cargo.dvalve:
            state = cargo.dvalve_task[dvalve.name]
            dvalve.set_state(state)

        # meta
        time.sleep(cargo.sampling_time)
        new_state = cargo.state
    return (new_state, cargo)


def reference_tracking(cargo):
    """ Track the reference from data.buffer """
    rootLogger.info("Arriving in REFERENCE_TRACKING State: ")
    cargo.actual_state = 'REFERENCE_TRACKING'

    while cargo.state == 'REFERENCE_TRACKING':
        for valve in cargo.valve:
            cargo.ref_task[valve.name] = 0.0

        idx = 0
        while (cargo.wcomm.confirm and
               cargo.state == 'REFERENCE_TRACKING' and
               (idx < cargo.wcomm.idx_threshold or
                cargo.wcomm.infmode)):
            cargo.wcomm.is_active = True
            rootLogger.info('walking is active')
            try:
                if idx == 0:
                    rootLogger.info('Do Initial Pattern')
                    cargo = process_pattern(cargo, INITIAL_PATTERN)
                rootLogger.info('Do Pattern of round {}'.format(idx))
                cargo = process_pattern(cargo, cargo.wcomm.pattern)
            except IOError:
                rootLogger.exception('IO doesnt care ...')
            rootLogger.info('wcomm finished round {}'.format(idx))
            idx += 1
        cargo.wcomm.confirm = False
        if cargo.wcomm.is_active:
            rootLogger.info('Do Final Pattern')
            cargo = process_pattern(cargo, FINAL_PATTERN)
            rootLogger.info('walking is not active')
        cargo.wcomm.is_active = False
        #
        time.sleep(cargo.sampling_time)
        new_state = cargo.state

        # write
        for valve, controller in zip(cargo.valve, cargo.controller):
            valve.set_pwm(1.)
            cargo.rec_r['r{}'.format(valve.name)] = None
            cargo.rec_u['u{}'.format(valve.name)] = 1.

        for dvalve in cargo.dvalve:
            dvalve.set_state(False)
    new_state = cargo.state
    return (new_state, cargo)


def process_pattern(cargo, pattern):
    """ Play the given pattern only once.

        Args:
            pattern(list): A list of lists of references

        Example:
            WCommander.process_pattern([[ref11, ref12, ..., ref1N, tmin1],
                                        [ref21, ref22, ..., ref2N, tmin2],
                                        ...
                                        [refM1, refM2, ..., refMN, tminM]])
    """
    n_valves = len(cargo.valve)
    n_dvalves = len(pattern[0]) - 1 - n_valves

    for pos in pattern:
        # read the refs
        local_min_process_time = pos[-1]
        ppos = pos[:n_valves]
        dpos = pos[-n_dvalves-1:-1]

        # set d valves
        for dvalve in cargo.dvalve:
            state = dpos[int(dvalve.name)]
            dvalve.set_state(state)
        
        # hold the thing for local_min_process_time
        tstart = time.time()
        while time.time() - tstart < local_min_process_time:
            # read
            for sensor in cargo.sens:
                cargo.rec[sensor.name] = sensor.get_value()

            # write
            for valve, controller in zip(cargo.valve, cargo.controller):
                ref = ppos[int(valve.name)]
                sys_out = cargo.rec[valve.name]
                ctr_out = controller.output(ref, sys_out)
                valve.set_pwm(ctrlib.sys_input(ctr_out))
                cargo.rec_r['r{}'.format(valve.name)] = ref
                cargo.rec_u['u{}'.format(valve.name)] = ctr_out
            # meta
            time.sleep(cargo.sampling_time)
    return cargo



def error_state(cargo):
    """ Catching unexpected Errors and decide what to do """
    rootLogger.info("Arriving in ERROR State: ")
    cargo.actual_state = 'ERROR'

    rootLogger.exception("Unexpected error:\n", cargo.errmsg[0])
    rootLogger.exception(cargo.errmsg[1])
#    traceback.print_tb(cargo.errmsg[2])

    return ('PAUSE', cargo)


def exit_cleaner(cargo):
    """ Clean everything up """
    rootLogger.info("cleaning ...")
    cargo.actual_state = 'EXIT'

    for idx, valve in enumerate(cargo.valve):
        valve.set_pwm(1.)
        if idx == 0:
            valve.cleanup()
    for dvalve in cargo.dvalve:
        dvalve.cleanup()

    return ('QUIT', cargo)


class Cargo(object):
    """
    The Cargo, which is transported from state to state
    """
    def __init__(self, state, sens=[], valve=[], dvalve=[],
                 controller=[]):
        self.state = state
        self.actual_state = state
        self.sens = sens
        self.valve = valve
        self.dvalve = dvalve
        self.controller = controller
        self.errmsg = None
        self.sampling_time = TSAMPLING
        self.pwm_task = {}
        self.dvalve_task = {}
        for dv in dvalve:
            self.dvalve_task[dv.name] = 0.
        self.ref_task = {}
        for v in valve:
            self.ref_task[v.name] = 0.
            self.pwm_task[v.name] = 0.
        self.rec_u = {}
        self.rec_r = {}
        self.rec = {}
        self.maxpressure = MAX_PRESSURE
        self.maxctrout = MAX_CTROUT
        for sensor in sens:
            self.rec[sensor.name] = sensor.get_value()
        for valve in self.valve:
            self.rec_u['u{}'.format(valve.name)] = 1.
            self.rec_r['r{}'.format(valve.name)] = None

        self.wcomm = WCommCargo()
        self.simpleWalkingCommander = \
            walk_commander.SimpleWalkingCommander(self)


class WCommCargo(object):
    def __init__(self):
        self.pattern = PATTERN
        self.confirm = False
        self.is_active = False
        self.idx_threshold = 3
        self.infmode = False


if __name__ == '__main__':
    main()
