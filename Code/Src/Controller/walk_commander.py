# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 14:30:43 2017

@author: ls

related to:
https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python

"""
import threading
import time

from Src.Management import timeout
from Src.Management import exception
from Src.Management import state_machine
from Src.Controller import controller as ctrlib

TOL = 0.05




class SimpleWalkingCommander(object):
    def __init__(self, cargo):
        """ Minimal Walking Commander """
        self.cargo = cargo


    def process_pattern(self, pattern):
        """ Play the given pattern only once.

            Args:
                pattern(list): A list of lists of references

            Example:
                WCommander.process_pattern([[ref11, ref12, ..., ref1N, tmin1],
                                            [ref21, ref22, ..., ref2N, tmin2],
                                            ...
                                            [refM1, refM2, ..., refMN, tminM]])
        """
        n_valves = len(self.cargo.valve)
        n_dvalves = len(pattern[0]) - 1 - n_valves

        for pos in pattern:
            # read the refs
            local_min_process_time = pos[-1]
            ppos = pos[:n_valves]
            dpos = pos[-n_dvalves-1:-1]

            # set d valves
            for dvalve in self.cargo.dvalve:
                state = dpos[int(dvalve.name)]
                dvalve.set_state(state)
            
            # hold the thing for local_min_process_time
            tstart = time.time()
            while time.time() - tstart < local_min_process_time:
                # read
                for sensor in self.cargo.sens:
                    self.cargo.rec[sensor.name] = sensor.get_value()
    
                # write
                for valve, controller in zip(self.cargo.valve, self.cargo.controller):
                    ref = ppos[int(valve.name)]
                    sys_out = self.cargo.rec[valve.name]
                    ctr_out = controller.output(ref, sys_out)
                    valve.set_pwm(ctrlib.sys_input(ctr_out))
                    self.cargo.rec_r['r{}'.format(valve.name)] = ref
                    self.cargo.rec_u['u{}'.format(valve.name)] = ctr_out
                # meta
                time.sleep(self.cargo.sampling_time)







class Walking_Commander(object):
    def __init__(self, cargo):
        """ This class controls all extremities. It starts as many threads
        as poroprtional valves exists and communicate with those threads.
        This class should provide a handsome interface to track references.

            Args:
                cargo(Controller.Cargo): contains all hardware representations
        """

        self.timeout = 10    # [sec] until Exceptions is raised (must be int)
        self.minimum_process_time = 1.0  # [sec] until next pose is set
        self.pthreads = []
        self.status = [None]*len(cargo.valve)
        self.cargo = cargo
        self._init_threads()

    def _init_threads(self):
        """ initialize the PThreads """
        for v, s, c, i in zip(self.cargo.valve, self.cargo.sens,
                              self.cargo.controller,
                              range(len(self.cargo.valve))):
            self.pthreads.append(Thread_ProportinalValve(
                v, s, c, i, self.status, self.cargo.rec, self.cargo.rec_r,
                self.cargo.rec_u, self.cargo.sampling_time))

    def _set_pos(self, pos):
        """ Interface self.pthreads. Send the references for extremities
        to the Proportional Threads.

            Args:
                pos(list): references for all extremities

            Example:
                WalkingCommander._set_pos([ref1, ref2, ..., refN]) """
        for p, thread in zip(pos, self.pthreads):
            thread.set_ref(p)

    def _set_dpos(self, dpos):
        """ Interface discrete valve.

            Args:
                pos(list): references for all dvalves """
        for dvalve, state in zip(self.cargo.dvalve, dpos):
            dvalve.set_state(state)

    def process_pattern(self, pattern):
        """ Play the given pattern only once.

            Args:
                pattern(list): A list of lists of references

            Example:
                WCommander.process_pattern([[ref11, ref12, ..., ref1N, tmin1],
                                            [ref21, ref22, ..., ref2N, tmin2],
                                            ...
                                            [refM1, refM2, ..., refMN, tminM]])
        """
        n_valves = len(self.cargo.valve)
        n_dvalves = len(pattern[0]) - 1 - n_valves

        for pos in pattern:
            local_min_process_time = pos[-1]
            ppos = pos[:n_valves]
            dpos = pos[-n_dvalves-1:-1]
            self._set_pos(ppos)
            self._set_dpos(dpos)
            time.sleep(max(self.minimum_process_time, local_min_process_time))
            try:
                self._wait()
            except exception.TimeoutError:
                print 'took more than', self.timeout, 'sec to reach', pos
                print 'continue anyway'
                continue

    def run_threads(self):
        """ Run all PThreads """
        for thread in self.pthreads:
            thread.start()

    def clean(self):
        """ Close all PThreads """
        try:
            self._set_pos([0.]*len(self.pthreads))
            self._wait()
        except exception.TimeoutError:
            print "TimeOut while cleaning Pthreads... Shut down anyway"
        finally:
            for thread in self.pthreads:
                thread.stop()
                thread.join()

    def _wait(self):
        """ waiting until all PThreads have reached the desired reference """
        with timeout.timeout(self.timeout, 'PThreads TimeOut'):
            while 'PROCESS' in self.status:
                time.sleep(self.cargo.sampling_time)


class Thread_ProportinalValve(threading.Thread):
    def __init__(self, valve, sensor, controller, ident, status, rec, rec_r,
                 rec_u, sampling_time):
        """ This class provide the autonomous ability to act for every muscle
        of the soft robot.
        You can set a reference and the Thread will bring the muscle to it
        and stay there until you set another one.
        Furthermore this Thread has a kind of stop_button. Everybody can push
        it and cancel the Thread this way.

        Thread class with a stop() method. The thread itself has to check
        regularly for the stopped() condition.

            Args:
                valve(Actuators.ProportionalValve): valve this Thread
                    should control
                sensor(Sensor.PressureSensor): sensor which belongs to valve
                controller(Controller.Controller): plug in what you like
                ident(int): ID of valve in context of WalkingCommander class
                status(list): list of status for the WalkingCommander himself
                rec(dict): The Recorder of the server
        """

        super(Thread_ProportinalValve, self).__init__()
        self.valve = valve
        self.sensor = sensor
        self.controller = controller
        self.rec = rec
        self.rec_r = rec_r
        self.rec_u = rec_u
        self.sampling_time = sampling_time
        self._stop_event = threading.Event()
        self.status = status
        self.id = ident
        self.status[self.id] = 'initialized'

        self.ref = 0.0
        self.ref_old = 0.0
        self.tol = TOL
        self.automat = state_machine.StateMachine()
        self.automat.add_state('HOLD', self._hold)
        self.automat.add_state('PROCESS', self._process)
        self.automat.add_state('EXIT', None, end_state=True)
        self.automat.set_start('HOLD')

    def stop(self):
        """ Push this button to bring the Thread down in the near future """
        self._stop_event.set()
        print 'PThread', self.id, 'stopped', self.stopped()

    def stopped(self):
        """ In case somebody is interested if stop-button was pushed """
        return self._stop_event.is_set()

    def set_ref(self, ref):
        """ Interface to the WalkingCommander, s.t. the reference can be set"""
        self.ref_old = self.ref
        self.ref = ref

    def run(self):
        """ Start the StateMachine and call clean() after """
        self.status[self.id] = 'running'
        self.automat.run(cargo=None)
        self._clean()

    def _hold(self, cargo):
        """ Hold the reference as long as WalkingCommander set a new one"""

        # print 'PThread', self.id, 'hold ref:', self.ref

        self.status[self.id] = 'HOLD'
        while self.ref == self.ref_old and not self.stopped():
            sys_out = self.sensor.get_value()
            self.rec[self.sensor.name] = sys_out
            ctr_out = self.controller.output(self.ref, sys_out)
            sys_in = ctrlib.sys_input(ctr_out)
            self.valve.set_pwm(sys_in)
            self.rec_r['r{}'.format(self.valve.name)] = self.ref
            self.rec_u['u{}'.format(self.valve.name)] = ctr_out
            time.sleep(self.sampling_time)

        if self.stopped():
            new_state = 'EXIT'
        else:
            new_state = 'PROCESS'

        # print 'PThread', self.id, 'goes to:', new_state
        return (new_state, cargo)

    def _process(self, cargo):
        """ Bring the muscle to the disered Reference and if reached go
        back to HOLD """
        # print 'PThread', self.id, 'process to new ref:', self.ref
        self.ref_old = self.ref
        self.status[self.id] = 'PROCESS'
        sys_out = self.sensor.get_value()

        while not isclose(sys_out, self.ref, tol=self.tol) and \
                not self.stopped() and self.ref == self.ref_old:
            sys_out = self.sensor.get_value()
            self.rec[self.sensor.name] = sys_out
            ctr_out = self.controller.output(self.ref, sys_out)
            sys_in = ctrlib.sys_input(ctr_out)
            self.valve.set_pwm(sys_in)
            self.rec_r['r{}'.format(self.valve.name)] = self.ref
            self.rec_u['u{}'.format(self.valve.name)] = ctr_out
            time.sleep(self.sampling_time)

        if self.stopped():
            new_state = 'EXIT'
        elif self.ref != self.ref_old:
            new_state = 'PROCESS'
        else:
            new_state = 'HOLD'

#        print 'PThread', self.id, 'goes to:', new_state
        return (new_state, cargo)

    def _clean(self):
        """ clean everything before closing the thread """
        self.status[self.id] = 'cleaning'
        self.valve.set_pwm(0)


def isclose(a, b, rel_tol=1e-09, tol=0.0):
    """ Use to compare if two floats are close to each other. From:
    https://stackoverflow.com/questions/5595425/what-is-the-best-way-to-compare-floats-for-almost-equality-in-python

        Args:
            a (float): First float to compare
            b (float): Second float to compare
            rel_tol(opt float): is a relative tolerance, it is multiplied by
                the greater of the magnitudes of the two arguments; as the
                values get larger, so does the allowed difference between them
                while still considering them equal.
            abs_tol(opt float):  is an absolute tolerance that is applied as-is
                in all cases. If the difference is less than either of those
                tolerances, the values are considered equal. """
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), tol)
