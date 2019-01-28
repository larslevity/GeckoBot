"""
module for data management
"""

import time

def merge_multiple_dicts(dicts):
    super_dict = {}
    for d in dicts:
        for key, value in d.iteritems():
            super_dict[key] = value
    return super_dict


def rehash_record(pressure=[None]*8, reference=[None]*8, motor_in=[None]*8,
                  fixation=[None]*4, alphaIMG=[None]*6, epsilon=None, 
                  positionx=[None]*6, positiony=[None]*6, 
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
#                self.recorded[key+'_t'] = {'val': [], 'len': 0}
                in_rec = False
            self.recorded[key]['val'].append(sample[key])
#            self.recorded[key+'_t']['val'].append(time.time()-self.start_time)
            self.recorded[key]['len'] += 1
#            self.recorded[key+'_t']['len'] += 1
            if self.recorded[key]['len'] > self.max_idx:
                self.max_idx = self.recorded[key]['len']
        return in_rec
