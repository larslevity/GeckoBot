"""
module for data management
"""

import time
from collections import deque


def merge_multiple_dicts(dicts):
    super_dict = {}
    for d in dicts:
        for key, value in iter(d.items()):
            super_dict[key] = value
    return super_dict


def rehash_record(pressure=[None]*8, reference=[None]*8, motor_in=[None]*8,
                  fixation=[None]*4, alphaIMG=[None]*6, epsilon=None,
                  positionx=[None]*7, positiony=[None]*7,
                  alphaIMU=[None]*6, IMU=False, IMG=False):

    p = {'p{}'.format(idx): px for idx, px in enumerate(pressure)}
    r = {'r{}'.format(idx): px for idx, px in enumerate(reference)}
    u = {'u{}'.format(idx): px for idx, px in enumerate(motor_in)}
    f = {'f{}'.format(idx): px for idx, px in enumerate(fixation)}
    t = {'time': time.time()}

    record = merge_multiple_dicts([p, r, u, f, t])
    if IMG:
        aIMG = {'aIMG{}'.format(idx): px for idx, px in enumerate(alphaIMG)}
        x = {'x{}'.format(idx): px for idx, px in enumerate(positionx)}
        y = {'y{}'.format(idx): px for idx, px in enumerate(positiony)}
        eps = {'eps': epsilon}
        record = merge_multiple_dicts([record, aIMG, x, y, eps])
    if IMU:
        aIMU = {'aIMU{}'.format(idx): px for idx, px in enumerate(alphaIMU)}
        record = merge_multiple_dicts([record, aIMU])

    return record


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
        self.StartStop = False
        self.StartStopIdx = [None, None]
        self.record = False
        self.record_file = None

    def append(self, sample, maxlen=1000):
        """
        Append a sample to recorder.

        Args:
            sample (dict): Dictionary of all recorded values in a sample
        """
        in_rec = True
        for key in sample:
            if key not in self.recorded:
                self.recorded[key] = {'val': deque([], maxlen), 'len': 0}
                in_rec = False
            self.recorded[key]['val'].append(sample[key])
            self.recorded[key]['len'] += 1
            if self.recorded[key]['len'] > self.max_idx:
                val_len = self.recorded[key]['len']
                self.max_idx = val_len if val_len < maxlen else maxlen
        return in_rec
