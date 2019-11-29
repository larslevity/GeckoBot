# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 09:27:59 2019

@author: AmP
"""
import socket
import time


from Src.Hardware import user_interface
from Src.Hardware import lcd as lcd_module
from Src.Communication import pickler
from Src.Management.thread_communication import ui_state
from Src.Management import timeout
from Src.Management import exception

lcd = lcd_module.getlcd()


def main(connection):
    def send_back(data_out):
        data_out_raw = pickler.pickle_data(data_out)
        connection.sendall(data_out_raw)

    exit_flag = False

    while not exit_flag:
        task_raw = connection.recv(4096)
        task = pickler.unpickle_data(task_raw)

        if task[0] == 'get':
            send_back(ui_state.get())
        elif task[0] == 'display':
            msg = task[1]
            lcd.display(msg)
        elif task[0] == 'Exit':
            exit_flag = True
            break
        elif task[0] == 'select from list':
            lis = task[1]
            Q = task[2]
            time_to_answer = task[3]
            with timeout.timeout(time_to_answer):
                try:
                    ans = lcd.select_elem_from_list(lis, Quest=Q)
                except exception.TimeoutError:
                    lcd.display('time out ...')
                    lcd.display('')
                    ans = None
            send_back(ans)

        elif task[0] == 'select from keylist':
            keylist = task[1]
            default = task[2]
            ans = lcd.select_from_keylist(keylist, default)
            send_back(ans)

        time.sleep(.05)
    return 0


if __name__ == '__main__':
    lcd.display('starting server ...')
    # Start a socket listening for connections on 0.0.0.0:8000
    server_socket = socket.socket()
    server_socket.bind(('', 12397))
    server_socket.listen(0)

    # Accept a single connection and make a file-like object out of it
    conn = server_socket.accept()[0]
    connection = conn.makefile('rb')

    lcd.display('connected ...')

    # initialize UI
    UIThread = user_interface.UserInterface()
    UIThread.start()
    
    try:
        lcd.display('starting comm thread ...')
        main(conn)
    finally:
        lcd.display('program ends ...')
        connection.close()
        UIThread.kill()
        server_socket.close()
        time.sleep(.5)
        lcd.turn_off()
