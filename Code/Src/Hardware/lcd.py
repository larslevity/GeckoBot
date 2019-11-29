# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 10:20:17 2019

@author: AmP
"""

import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as char_lcd
import time

from Src.Management.thread_communication import ui_state


class _LCD(object):
    def __init__(self):
        cols = 16
        rows = 2
        i2c = busio.I2C(board.SCL, board.SDA)
        self.lcd = char_lcd.Character_LCD_RGB_I2C(i2c, cols, rows)
        self.lcd.color = [100, 0, 0]
        self.lcd.message = 'Moin!'

    def display(self, msg, clear=True):
        if clear:
            self.lcd.clear()
        self.lcd.message = msg

    def turn_off(self):
        self.lcd.color = [0, 0, 0]
        self.lcd.clear()

    def select_from_keylist(self, list_of_keys, default_key=None):

        ui_mode_start = ui_state.mode

        selected_key = None
        if default_key:
            if default_key in list_of_keys:
                idx = list_of_keys.index(default_key)
            else:
                idx = 0
        else:
            idx = 0
        self.display(list_of_keys[idx])
        while selected_key is None:
            if self.lcd.up_button:
                idx = idx - 1 if idx > 0 else len(list_of_keys) - 1
                self.display(list_of_keys[idx], clear=1)
            elif self.lcd.down_button:
                idx = idx + 1 if idx < len(list_of_keys) - 1 else 0
                self.display(list_of_keys[idx], clear=1)
            elif self.lcd.select_button or ui_state.fun[0]:
                self.display("SELECTED")
                selected_key = list_of_keys[idx]
            elif ui_mode_start != ui_state.mode:
                break
            time.sleep(.1)

        self.lcd.clear()
        return selected_key

    def select_elem_from_list(self, lis, default_key=None, Quest=''):
        list_of_elems = lis
        selected_elem = None
        if default_key:
            if default_key in list_of_elems:
                idx = list_of_elems.index(default_key)
            else:
                idx = 0
        else:
            idx = 0
        self.display(Quest+'\n'+list_of_elems[idx])
        while selected_elem is None:
            if self.lcd.up_button:
                idx = idx - 1 if idx > 0 else len(list_of_elems) - 1
                self.display('\n'+list_of_elems[idx], clear=0)
            elif self.lcd.down_button:
                idx = idx + 1 if idx < len(list_of_elems) - 1 else 0
                self.display('\n'+list_of_elems[idx], clear=0)
            elif self.lcd.select_button:
                self.display("SELECTED")
                selected_elem = list_of_elems[idx]
            time.sleep(.1)
        self.lcd.clear()
        return selected_elem


lcd = _LCD()


def getlcd():
    return lcd
