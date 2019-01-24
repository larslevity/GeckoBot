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
