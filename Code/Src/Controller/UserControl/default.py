# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 15:51:41 2019

@author: AmP
"""

from Src.Management.thread_communication import llc_ref
from Src.Management import load_pattern as load_ptrn


n_pc = len(llc_ref.pressure)

# Names of Modes
NAMES = ['PWM', 'PRESSURE', 'GECKO']


def mode1(switches, potis, fun):
    llc_ref.set_state('FEED_THROUGH')
    for idx in potis:
        potis[idx] = potis[idx]*100
    llc_ref.pwm = potis
    llc_ref.dvalve = switches


def mode2(switches, potis, fun):

    llc_ref.set_state('PRESSURE_REFERENCE')

    if not fun[0]:
        llc_ref.pressure = potis
    else:
        llc_ref.pressure = {idx: 0.0 for idx in range(n_pc)}
    llc_ref.dvalve = switches


def mode3(switches, potis, fun):
    llc_ref.set_state('PRESSURE_REFERENCE')








class SharedMemory(object):
    """ Data, which is shared between Threads """
    def __init__(self):
        self.sampling_time = .01

        self.ptrndic = {
            name: load_ptrn.read_list_from_csv('Patterns/'+name)
            for name in load_ptrn.get_csv_files()}
        self.ptrndic['selected'] = sorted(list(self.ptrndic.keys()))[0]
        self.pattern = self.ptrndic[self.ptrndic['selected']]