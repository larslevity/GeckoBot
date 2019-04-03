# -*- coding: utf-8 -*-
"""
Created on Tue Feb 06 09:12:16 2018

@author: AmP


for Raspberry 3
"""

import smbus
import time
import numpy as np



class MultiPlexer(object):
    def __init__(self, address=0x70):
        self.bus = smbus.SMBus(1)    # bus = smbus.SMBus(0) fuer Revision 1
        self.address = address
        
    def select(self, port_id):
        self.bus.write_byte(self.address, 1 << port_id)


class CLB_file(object):
    def __init__(self):
        self.S = None
        self.Sinv = None
        self.b = None
        self.T = None
        self.TS = None
        self.s = None
        self.is_clb = False

       
class GY_521(object):
    plexer = MultiPlexer()
    
    def __init__(self, plx_id, name=None, address=0x68):
        self.name = name

        self.address = address  # i2c address
        power_mgmt_1 = 0x6b     # power management of IMU
        self.cntl = 0x0a             # mag mode control
        self.plx_id = plx_id    # plex ID of IMU
        ra_int_pin_cfg = 0x37   # config reg of IMU
        # MultiPlexer schlaten, um das Modul ansprechen zu koennen
        self.plexer.select(self.plx_id)
        time.sleep(.1)
        # Power on of Acc
        self.plexer.bus.write_byte_data(self.address, power_mgmt_1, 0x00)
        time.sleep(.1)

    def _read_word(self, reg, mag=False):
        if mag:
            l = self.plexer.bus.read_byte_data(self.mag_adr, reg)
            h = self.plexer.bus.read_byte_data(self.mag_adr, reg+1)
        else:
            h = self.plexer.bus.read_byte_data(self.address, reg)
            l = self.plexer.bus.read_byte_data(self.address, reg+1)
        value = (h << 8) + l
        return value
 
    def _read_word_2c(self, reg, mag=False):
        val = self._read_word(reg, mag)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val


    def get_acceleration(self, raw=False):
        self.plexer.select(self.plx_id)
        acc_xout = self._read_word_2c(0x3b)
        acc_yout = self._read_word_2c(0x3d)
        acc_zout = self._read_word_2c(0x3f)

        return (acc_xout, acc_yout, acc_zout)
