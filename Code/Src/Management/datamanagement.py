"""
module for data management
"""

import time


class GUIRecorder(object):
    """
    GUIData provide a customized set of data structure for GUI
    control of the GeckoBot system.
    The GUIData is only for the GUI.
    """
    def __init__(self):
        """
        """
        self.recorded = {}
        self.max_idx = 0
        self.start_time = time.time()

    def append(self, sample):
        """
        Append a sample to recorder.

        Args:
            sample (dict): Dictionary of all recorded values in a sample
        """
        in_rec = True
        for key in sample:
            if key not in self.recorded:
                self.recorded[key] = {'val': [], 'len': 0}
                self.recorded[key+'_t'] = {'val': [], 'len': 0}
                in_rec = False
            self.recorded[key]['val'].append(sample[key])
            self.recorded[key+'_t']['val'].append(time.time()-self.start_time)
            self.recorded[key]['len'] += 1
            self.recorded[key+'_t']['len'] += 1
            if self.recorded[key]['len'] > self.max_idx:
                self.max_idx = self.recorded[key]['len']
        return in_rec


class GUITask(object):
    """
    Tasks from User to the stateMachine
    """
    def __init__(self, start_state, valve_data=[], dvalve_data=[],
                 max_pressure=None, max_ctrout=None, tsampling=None,
                 PID_gains=[[None for gain in range(3)] for ctr in range(6)],
                 pattern=[[0.0]*6+[False]*4]*2):
        self.state = start_state
        self.pwm = {}
        self.ref = {}
        self.dvalve_state = {}
        for valve_name in valve_data:
            self.pwm[valve_name] = 0
            self.ref[valve_name] = 0
        for dvalve_name in dvalve_data:
            self.dvalve_state[dvalve_name] = 0

        # Settings
        self.maxpressure = max_pressure
        self.set_maxpressure = False
        self.PID_Params = PID_gains
        self.set_PID = [False]*len(valve_data)
        self.maxctrout = max_ctrout
        self.set_maxctrout = False
        self.tsampling = tsampling
        self.set_tsampling = False

        # WalkingCommander
        self.pattern = pattern
        self.set_pattern = False
        self.walking_state = False
        self.set_walking_state = False
