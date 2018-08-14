# pylint: disable = invalid-name, no-member, fixme
""" Main function running on BBB
According to: https://pymotw.com/2/socket/tcp.html

---------------------------
In order to enable 'P9_28' as pwm pin, you have to load 'cape-universala' in
/boot/uEnv.txt by adding following line:

nano /boot/uEnv.txt
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
-- This is super weird! starting the script every time a error occurs again.


---------------------------

To see what happens in crontab, create a Crontab Logger:

crontab -e:
    @reboot /home/debian/Git/GeckoBot/boot_autorun_test/ssh_hack.sh 2>&1 |
        /home/debian/Git/GeckoBot/boot_autorun_test/timestamp.sh  >>
        /home/debian/Git/GeckoBot/boot_autorun_test/log/cronlog.log

---------------------------

ssh Hack:
For some reason the BBIO.PWM module needs a terminal (tty) to initialize.
A Job, started by crontab does not have a tty. There is simply no tty.
Therefore we ssh into the device from the device itself. So we create a virtual
tty.
To do so run the "ssh_hack.sh" script. it will automatically run the start
script.
But you must enable a ssh-login as root without password. 2 Steps:
#    1. disable root pw:
#        passwd -d root
#            (to clear the password)
#            editing
#        nano /etc/pam.d/common-auth
#            Find the "pam_unix.so" line and add "nullok" to the end if its
#            not there or change "nullok_secure" to be just "nullok" if
#            yours says nullok_secure.
    2. allow ssh to root login without password:
        Ref: https://askubuntu.com/questions/115151/how-to-set-up-passwordless-ssh-access-for-root-user
        Basically, we have to create a public key for root and copy it
        to the BBB itself. Just follow the
        instructions on Ref above.
        But dont set "PasswordAuthentication" to 'no'! Since than nobody can
        login with a password anymore, only with a public key. Which is not
        yet created anywhere else except on the BBB itself.

        nano /etc/ssh/sshd_config
            PermitRootLogin without-password
    3. restart ssh service:
        service ssh restart
    4. disable requiretty for root:
        visudo
        and add 'Defaults: root !requiretty'

    5. spawn a shell:
        Ref: https://netsec.ws/?p=337

#### stdin is no tty:
    https://michaelseiler.net/2013/04/25/cron-jobs-and-ssh-errors-tty-and-sudo/


https://sachinpradeeplinux.wordpress.com/2012/09/28/stdin-is-not-a-tty-error/
On the destination server, edit /root/.bashrc file and comment out
the "mesg y" line.

If it is no there, please add the following line to .bashrc file .

if `tty -s`; then
 mesg n
fi





"""
from __future__ import print_function

import sys
import time
import logging
import errno

from Src.Hardware import sensors as sensors
from Src.Hardware import actuators as actuators
from Src.Management import state_machine
from Src.Communication import hardware_control as HUI
from Src.Math import IMUcalc


from Src.Controller import walk_commander
from Src.Controller import controller as ctrlib


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


ptrn_v2_2 = HUI.generate_pattern(.80, 0.80, 0.90, 0.99, 0.80, 0.80, 0.0, 0.0)
ptrn_v2_3 = HUI.generate_pattern(.72, 0.74, 0.99, 0.99, 0.69, 0.63, 0.0, 0.0)
ptrn_v2_4 = HUI.generate_pattern(.64, 0.79, 0.99, 0.99, 0.75, 0.78, 0.0, 0.0)
ptrn_v2_5 = HUI.generate_pattern(.92, 0.68, 0.93, 0.92, 0.90, 0.74, 0.0, 0.0)
ptrn_v2_6 = HUI.generate_pattern(.77, 0.99, 0.97, 0.93, 0.70, 0.71, 0.0, 0.0)

# MAX_PRESSURE = 0.85    # [bar] v2.2
# MAX_PRESSURE = 0.93    # [bar] v2.3
# MAX_PRESSURE = 0.85      # [bar] v2.4



ptrn_v3_0 = HUI.generate_pattern(.63, 0.56, 0.99, 0.99, 0.55, 0.73, 0.0, 0.0)


ptrn_v3_0_straight_a = \
    HUI.generate_pattern(.68, 0.56, 0.99, 0.99, 0.67, 0.79, 0.0, 0.0)

ptrn_v3_0_straight_b = HUI.generate_pattern_curve(
        .65, 0.2, 0.00, 0.99, 0.2, 0.75, 0.0, 0.0,
        .2, 0.54, 0.99, 0.00, 0.64, 0.2, 0.0, 0.0)

ptrn_v3_0_straight_c = HUI.generate_pattern_curve(
        .2, 0.4, 0.00, 0.99, 0.25, 0.3, 0.0, 0.0,
        .4, 0.2, 0.99, 0.00, 0.3, 0.25, 0.0, 0.0)


ptrn_v3_0_curve_orginal = HUI.generate_pattern_curve(
        .71, 0.46, 0.00, 0.99, 0.72, 0.47, 0.0, 0.0,
        .58, 0.00, 0.00, 0.00, 0.56, 0.00, 0.0, 0.0)

ptrn_v3_0_curve_a = HUI.generate_pattern_curve(
        .7, 0.55, 0.00, 0.99, 0.73, 0.5, 0.0, 0.0,
        .39, 0.00, 0.00, 0.0, 0.56, 0.00, 0.0, 0.0)

ptrn_v3_0_curve_b = HUI.generate_pattern_curve(
        .7, 0.56, 0.00, 0.99, 0.78, 0.5, 0.0, 0.0,
        .39, 0.00, 0.00, 0.0, 0.46, 0.00, 0.0, 0.0)

ptrn_v3_0_curve_c = HUI.generate_pattern_curve(
        .9, 0.65, 0.00, 0.99, 0.99, 0.74, 0.0, 0.0,
        .0, 0.00, 0.00, 0.00, 0.00, 0.00, 0.0, 0.0)



ptrn_v3_pres = 1


MAX_PRESSURE = ptrn_v3_pres
DEFAULT_PATTERN = ptrn_v3_0_straight_a      # default pattern

MAX_CTROUT = 0.50     # [10V]
TSAMPLING = 0.001     # [sec]
PID = [1.05, 0.03, 0.01]    # [1]
PIDimu = [0.0117, 1.012, 0.31]

START_STATE = 'PAUSE'


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
    rootLogger.info("Initialize IMUs ...")
    # mplx address for IMU is 0x71
    IMU = []
    sets = [{'name': '0', 'id': 0},
            {'name': '1', 'id': 1},
            {'name': '2', 'id': 2},
            {'name': '3', 'id': 3},
            {'name': '4', 'id': 4},
            {'name': '5', 'id': 5}]
    try:
        for s in sets:
            IMU.append(sensors.MPU_9150(name=s['name'], mplx_id=s['id']))
    except IOError:  # not connected
         IMU = False
    rootLogger.info("IMU detected?: {}".format(not(not(IMU))))

    rootLogger.info("Initialize Pressure Sensors ...")
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

    return sens, valve, dvalve, IMU


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

    imu_controller = []
    sets = [{'name': '0', 'P': PIDimu[0], 'I': PIDimu[1], 'D': PIDimu[2]},
            {'name': '1', 'P': PIDimu[0], 'I': PIDimu[1], 'D': PIDimu[2]},
            {'name': '2', 'P': PIDimu[0], 'I': PIDimu[1], 'D': PIDimu[2]},
            {'name': '3', 'P': PIDimu[0], 'I': PIDimu[1], 'D': PIDimu[2]},
            {'name': '4', 'P': PIDimu[0], 'I': PIDimu[1], 'D': PIDimu[2]},
            {'name': '5', 'P': PIDimu[0], 'I': PIDimu[1], 'D': PIDimu[2]}]
    for elem in sets:
        imu_controller.append(
            ctrlib.PidController([elem['P'], elem['I'], elem['D']],
                                 tsamplingPID, maxoutPID))

    return controller, imu_controller


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
    sens, valve, dvalve, IMU = init_hardware()
    controller, imu_ctr = init_controller()

    rootLogger.info('Initialize the shared variables, i.e. cargo ...')
    start_state = START_STATE
    cargo = Cargo(start_state, sens=sens, valve=valve, dvalve=dvalve,
                  controller=controller, IMU=IMU, imu_ctr=imu_ctr)

    rootLogger.info('Setting up the StateMachine ...')
    automat = state_machine.StateMachine()
    automat.add_state('PAUSE', pause_state)
    automat.add_state('IMU_CONTROL', imu_control)
    automat.add_state('ERROR', error_state)
#    automat.add_state('REFERENCE_TRACKING', reference_tracking)
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
    except Exception as err:
        rootLogger.exception(
            '\n----------caught exception! in Main Thread----------------\n')
        rootLogger.exception("Unexpected error:\n", sys.exc_info()[0])
        rootLogger.exception(sys.exc_info()[1])
        rootLogger.error(err, exc_info=True)
        rootLogger.info('\n ----------------------- killing UI --')
        communication_thread.kill()

    communication_thread.join()
    rootLogger.info('All is done ...')
    sys.exit(0)


# HELP FUNCTIONS
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


def imu_set_ref(cargo):
    ''' Positions of IMUs:
    <       ^       >
    0 ----- 1 ----- 2
            |
            |
            |
    3 ------4 ------5
    <       v       >
    In IMUcalc.calc_angle(acc0, acc1, rot_angle), "acc0" is turned by rot_angle
    '''
    imu_idx = {'0': [0, 1, -90], '1': [1, 2, -90], '2': [1, 4, 180],
               '3': [4, 1, 180], '4': [4, 3, -90], '5': [5, 4, -90]}
#    s = ''
    imu_rec = cargo.rec_IMU
    for valve, controller in zip(cargo.valve, cargo.imu_ctr):
        ref = cargo.ref_task[valve.name]*90.
        idx0, idx1, rot_angle = imu_idx[valve.name]
        acc0 = imu_rec[str(idx0)]
        acc1 = imu_rec[str(idx1)]

        sys_out = IMUcalc.calc_angle(acc0, acc1, rot_angle)
        ctr_out = controller.output(ref, sys_out)
        pressure = cargo.rec[valve.name]
        pressure_bound = pressure_check(
                pressure, 1.5*cargo.maxpressure, 1*cargo.maxpressure)
        ctr_out_ = cutoff(ctr_out+pressure_bound)

#        ss = 'Channel[{}]\nangle: \t {}\tref: \t {}\tprss: \t {}\tpbound:\t {}\tdelta: \t {}\n'.format(
#                valve.name, round(sys_out*100)/100., ref, round(pressure*100)/100.,
#                round(pressure_bound*100)/100., round(delta*100)/100.)
#        s = s + ss
        # for torso, set pwm to 0 if other ref is higher:
        if valve.name in ['2', '3']:
            other = '2' if valve.name == '3' else '3'
            other_ref = cargo.ref_task[other]*90
            if ref == 0 and ref == other_ref:
                if pressure > .5:
                    ctr_out_ = -MAX_CTROUT
            elif ref < other_ref or (ref == other_ref and ref > 0):
                ctr_out_ = -MAX_CTROUT

        valve.set_pwm(ctrlib.sys_input(ctr_out_))
        cargo.rec_r['r{}'.format(valve.name)] = ref
        cargo.rec_u['u{}'.format(valve.name)] = ctr_out
#    s = s + '\n\n'
#    print(s)
    return cargo


def set_ref(cargo):
    for valve, controller in zip(cargo.valve, cargo.controller):
        ref = cargo.ref_task[valve.name]
        sys_out = cargo.rec[valve.name]
        ctr_out = controller.output(ref, sys_out)
        valve.set_pwm(ctrlib.sys_input(ctr_out))
        cargo.rec_r['r{}'.format(valve.name)] = ref
        cargo.rec_u['u{}'.format(valve.name)] = ctr_out
    return cargo


def set_dvalve(cargo):
    for dvalve in cargo.dvalve:
        state = cargo.dvalve_task[dvalve.name]
        dvalve.set_state(state)


def read_sens(cargo):
    for sensor in cargo.sens:
        try:
            cargo.rec[sensor.name] = sensor.get_value()
        except IOError as e:
            if e.errno == errno.EREMOTEIO:
                rootLogger.info(
                    'cant read i2c device.' +
                    ' Continue anyway ... Fail in [{}]'.format(sensor.name))
            else:
                rootLogger.exception('Sensor [{}]'.format(sensor.name))
                rootLogger.error(e, exc_info=True)
                raise e
    return cargo


def read_imu(cargo):
    for imu in cargo.IMU:
        try:
            cargo.rec_IMU[imu.name] = imu.get_acceleration()
        except IOError as e:
            if e.errno == errno.EREMOTEIO:
                rootLogger.exception(
                    'cant read imu device.' +
                    'Continue anyway ...Fail in [{}]'.format(imu.name))
            else:
                rootLogger.exception('Sensor [{}]'.format(imu.name))
                rootLogger.error(e, exc_info=True)
                raise e
    return cargo


def init_output(cargo):
    for valve in cargo.valve:
        valve.set_pwm(20.)
        cargo.rec_u['u{}'.format(valve.name)] = 20.
        cargo.rec_r['r{}'.format(valve.name)] = None
    return cargo


#  SET UP the state Handler
def imu_control(cargo):
    rootLogger.info("Arriving in IMU_CONTROL State: ")
    cargo.actual_state = 'IMU_CONTROL'

    cargo = init_output(cargo)
    while cargo.state == 'IMU_CONTROL':
        cargo = read_sens(cargo)
        if cargo.IMU:
            set_dvalve(cargo)
            cargo = read_imu(cargo)
            cargo = imu_set_ref(cargo)

        time.sleep(cargo.sampling_time)
        new_state = cargo.state
    return (new_state, cargo)


def pause_state(cargo):
    """
    do nothing. waiting for tasks
    """
    rootLogger.info("Arriving in PAUSE State: ")
    cargo.actual_state = 'PAUSE'
    cargo = init_output(cargo)

    while cargo.state == 'PAUSE':
        cargo = read_sens(cargo)
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
        cargo = read_sens(cargo)

        # write
        for valve in cargo.valve:
            pwm = cargo.pwm_task[valve.name]
            valve.set_pwm(pwm)
            cargo.rec_r['r{}'.format(valve.name)] = None
            cargo.rec_u['u{}'.format(valve.name)] = pwm/100.
        set_dvalve(cargo)
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
        cargo = read_sens(cargo)
        # write
        cargo = set_ref(cargo)
        set_dvalve(cargo)
        # meta
        time.sleep(cargo.sampling_time)
        new_state = cargo.state
    return (new_state, cargo)

#
#def reference_tracking(cargo):
#    """ Track the reference from data.buffer """
#    rootLogger.info("Arriving in REFERENCE_TRACKING State: ")
#    cargo.actual_state = 'REFERENCE_TRACKING'
#
#    cargo = init_output(cargo)
#
#    while cargo.state == 'REFERENCE_TRACKING':
#        idx = 0
#        while (cargo.wcomm.confirm and
#               cargo.state == 'REFERENCE_TRACKING' and
#               (idx < cargo.wcomm.idx_threshold or
#                cargo.wcomm.infmode)):
#            cargo.wcomm.is_active = True
#            rootLogger.info('walking is active')
#            if idx == 0:
#                rootLogger.info('Do Initial Pattern')
#                cargo = process_pattern(cargo, initial=True)
#            rootLogger.info('Do Pattern of round {}'.format(idx))
#            cargo = process_pattern(cargo)
#            rootLogger.info('wcomm finished round {}'.format(idx))
#            idx += 1
#        cargo.wcomm.confirm = False
#        if cargo.wcomm.is_active:
#            rootLogger.info('Do Final Pattern')
#            cargo = process_pattern(cargo, final=True)
#            rootLogger.info('walking is not active')
#        cargo.wcomm.is_active = False
#        # clean
#        time.sleep(cargo.sampling_time)
#        new_state = cargo.state
#        cargo = init_output(cargo)
#        for dvalve in cargo.dvalve:
#            dvalve.set_state(False)
#    new_state = cargo.state
#    return (new_state, cargo)
#
#
#def process_pattern(cargo, initial=False, final=False):
#    """ Play the given pattern only once.
#
#        Args:
#            pattern(list): A list of lists of references
#
#        Example:
#            WCommander.process_pattern([[ref11, ref12, ..., ref1N, tmin1],
#                                        [ref21, ref22, ..., ref2N, tmin2],
#                                        ...
#                                        [refM1, refM2, ..., refMN, tminM]])
#    """
#    if initial:
#        pattern = initial_pattern(cargo.wcomm.pattern)
#    elif final:
#        pattern = final_pattern(cargo.wcomm.pattern)
#    else:
#        pattern = cargo.wcomm.pattern
#    n_valves = len(cargo.valve)
#    n_dvalves = len(pattern[0]) - 1 - n_valves
#
#    for idx, pos in enumerate(pattern):
#        # read the refs
#        local_min_process_time = pos[-1]
#        dpos = pos[-n_dvalves-1:-1]
#        for jdx, dp in enumerate(dpos):
#            cargo.dvalve_task[str(jdx)] = dp
#        set_dvalve(cargo)
#
#        # hold the thing for local_min_process_time
#        tstart = time.time()
#        while time.time() - tstart < local_min_process_time:
#            cargo = read_sens(cargo)
#            for valve in cargo.valve:
#                cargo.ref_task[valve.name] = \
#                    cargo.wcomm.pattern[idx][:n_valves][int(valve.name)]
#            cargo = set_ref(cargo)
#            # meta
#            time.sleep(cargo.sampling_time)
#    return cargo


def error_state(cargo):
    """ Catching unexpected Errors and decide what to do """
    rootLogger.info("Arriving in ERROR State: ")
    cargo.actual_state = 'ERROR'

    rootLogger.exception("Unexpected error:\n", cargo.errmsg[0])
    rootLogger.exception(cargo.errmsg[1])

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
                 controller=[], IMU=[], imu_ctr=[]):
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
        self.IMU = IMU
        self.imu_ctr = imu_ctr
        for dv in dvalve:
            self.dvalve_task[dv.name] = 0.
        self.ref_task = {}
        for v in valve:
            self.ref_task[v.name] = 0.
            self.pwm_task[v.name] = 0.
        self.rec_u = {}
        self.rec_r = {}
        self.rec = {}
        self.rec_IMU = {}
        self.maxpressure = MAX_PRESSURE
        self.maxctrout = MAX_CTROUT
        for sensor in sens:
            self.rec[sensor.name] = 0.0
        if IMU:
            for imu in IMU:
                self.rec_IMU[imu.name] = imu.get_acceleration()
        for valve in self.valve:
            self.rec_u['u{}'.format(valve.name)] = 1.
            self.rec_r['r{}'.format(valve.name)] = None

        self.wcomm = WCommCargo()
        self.simpleWalkingCommander = \
            walk_commander.SimpleWalkingCommander(self)


class WCommCargo(object):
    def __init__(self):
        self.pattern = DEFAULT_PATTERN
        self.ptrndic = {'default': DEFAULT_PATTERN,
                        'usr_ptrn': HUI.generate_pattern(
                                0, 0, 0, 0, 0, 0, 0, 0)}
        self.confirm = False
        self.is_active = False
        self.idx_threshold = 3
        self.infmode = True  # default: walk forever
        self.user_pattern = False


def initial_pattern(ptrn):
    return [ptrn[-1][:8] + [False, False, False, False, 1.0],
            ptrn[-1][:8] + [False, True, True, False, .66]]


def final_pattern(ptrn):
    return [ptrn[-1][:8] + [False, True, True, False, 2.0],
            [0.]*8 + [False]*4 + [.25]]


if __name__ == '__main__':
    main()
