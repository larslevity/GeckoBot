# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 09:43:14 2019

@author: AmP
"""


from subprocess import call
import time

from Src.Communication.client import Socket
from Src.Management.thread_communication import ui_state

UI_ip = '192.168.5.2'


def start_UI(ip):
    cmd = 'ssh -i ~/.ssh/key_CBoardBBB_main root@{} nohup python3\
        /root/Git/GeckoBot/Code/UI_main.py &'.format(ip)
    call(cmd, shell=True)


class UISocket(Socket):
    def __init__(self, ip):
        Socket.__init__(self, ip)

    def get_data(self):
        self.send_all(['get'])
        data = self.recieve_data()
        return data


if __name__ == "__main__":

    print('main: starting UI Server...')
    start_UI(UI_ip)
    time.sleep(5)

    print('main: try to connect to UI_BBB...')
    ui_sock = UISocket(UI_ip)
    time.sleep(1)

    print('main: starting main loop...')
    try:
        while True:
            ui_state.set_state(ui_sock.get_data())
            print(ui_state)

    except KeyboardInterrupt:
        ui_sock.close()
    finally:
        ui_sock.close()
