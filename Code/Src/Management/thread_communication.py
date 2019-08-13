# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 10:46:32 2019

@author: AmP
"""

# from queue import Queue
from Src.Hardware.configuration import CHANNELset
from Src.Hardware.configuration import DiscreteCHANNELset
from Src.Hardware.configuration import IMUset
from Src.Hardware.configuration import STARTSTATE


class Borg:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class LLCReference(Borg):
    def __init__(self):
        Borg.__init__(self)

        self.dvalve = {name: 0. for name in DiscreteCHANNELset}
        self.pressure = {name: 0. for name in CHANNELset}
        self.pwm = {name: 20. for name in CHANNELset}
        self.state = STARTSTATE

    def set_state(self, state):
        """ a state in ['PAUSE', 'ANGLE_REFERENCE', 'FEED_THROUGH',
        'PRESSURE_REFERENCE', 'EXIT']
        """
        if state in ['PAUSE', 'ANGLE_REFERENCE',
                     'FEED_THROUGH', 'PRESSURE_REFERENCE', 'EXIT']:
            self.state = state
        else:
            raise KeyError('invalid state reference')


llc_ref = LLCReference()


class LLCRecorder(Borg):
    def __init__(self):
        Borg.__init__(self)

        self.p = {name: 0.0 for name in CHANNELset}
        self.aIMU = {name: None for name in IMUset}
        self.u = {name: 0.0 for name in CHANNELset}


llc_rec = LLCRecorder()


class IMGProcRecorder(Borg):
    def __init__(self):
        Borg.__init__(self)

        self.aIMG = {name: None for name in range(8)}
        self.X = {name: None for name in range(8)}  # 6 markers
        self.Y = {name: None for name in range(8)}
        self.eps = None
        self.xref = (None, None)


imgproc_rec = IMGProcRecorder()


class SystemConfig(Borg):
    def __init__(self):
        Borg.__init__(self)

        self.IMUsConnected = None
        self.Camera = None
        self.ImgProc = None
        self.LivePlotter = None
        self.ConsolePrinter = False

    def __str__(self):
        return (
"""
System Configuration as follows:
IMUs:\t\t {}connected
Camera:\t\t {}connected
ImgProc:\t {}connected
LivePlotter:\t {}connected
ConsolePrinter:\t {}abled
""".format(
    '' if self.IMUsConnected else 'not ', '' if self.Camera else 'not ',
    '' if self.ImgProc else 'not ', '' if self.LivePlotter else 'not ',
    'en' if self.ConsolePrinter else 'dis'))


sys_config = SystemConfig()


class UIState(Borg):
    def __init__(self):
        Borg.__init__(self)

        self.fun = [False, False]
        self.mode = 'MODE1'
        self.switches = {idx: False for idx in range(4)}
        self.potis = {idx: 0.0 for idx in range(7)}


ui_state = UIState()


#class LLCRecorder(object):
#    def __init__(self):
#        self.rec_p = Queue(1)
#        self.rec_p.put({name: 0.0 for name in CHANNELset})
#        self.rec_aIMU = Queue(1)
#        self.rec_aIMU.put({name: None for name in IMUset})
#        self.rec_u = Queue(1)
#        self.rec_u.put({name: 0.0 for name in CHANNELset})
#class LLCReference(object):
#    def __init__(self):
#        self.dvalve_ref = Queue(1)
#        self.dvalve_ref.put({name: 0. for name in DiscreteCHANNELset})
#        self.pressure_ref = Queue(1)
#        self.pressure_ref.put({name: 0. for name in CHANNELset})
#        self.pwm_ref = Queue(1)
#        self.pwm_ref.put({name: 20. for name in CHANNELset})
