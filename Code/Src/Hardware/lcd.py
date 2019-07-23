# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 10:20:17 2019

@author: AmP
"""

import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as char_lcd
import time


class LCD(object):
    def __init__(self):
        cols = 16
        rows = 2
        i2c = busio.I2C(board.SCL, board.SDA)
        self.lcd = char_lcd.Character_LCD_RGB_I2C(i2c, cols, rows)
        self.lcd.color = [100, 0, 0]
        self.lcd.message = 'Display initialized!'

    def select_from_dic(self, dic, default_key=None):
        list_of_keys = [name for name in sorted(iter(dic.keys()))]
        list_of_keys.remove('selected')  # due to api GeckoBot
        selected_key = None
        if default_key:
            idx = list_of_keys.index(default_key)
        else:
            idx = 0
        self.lcd.message = list_of_keys[idx]
        while selected_key is None:
            if self.lcd.up_button:
                idx = idx - 1 if idx > 0 else len(list_of_keys) - 1
                self.lcd.clear()
                self.lcd.message = list_of_keys[idx]
            elif self.lcd.down_button:
                idx = idx + 1 if idx < len(list_of_keys) - 1 else 0
                self.lcd.clear()
                self.lcd.message = list_of_keys[idx]
            elif self.lcd.select_button:
                self.lcd.clear()
                self.lcd.message = "SELECTED"
                selected_key = list_of_keys[idx]
                selected_val = dic[selected_key]
            time.sleep(.2)

        self.lcd.clear()
        return selected_val
