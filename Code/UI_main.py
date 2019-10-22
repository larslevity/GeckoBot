# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 09:27:59 2019

@author: AmP
"""
import socket
import time


from Src.Hardware import user_interface
from Src.Visual.PiCamera import pickler
from Src.Management.thread_communication import ui_state


def main(connection):
    def send_back(data_out):
        data_out_raw = pickler.pickle_data(data_out)
        connection.sendall(data_out_raw)

    def kill(self):
        self.exit_flag = True

    while True:
        task_raw = connection.recv(4096)
        task = pickler.unpickle_data(task_raw)

        if task[0] == 'get':
            send_back(ui_state.get())
        elif task[0] == 'Exit':
            break

        time.sleep(.05)


if __name__ == '__main__':
    # Start a socket listening for connections on 0.0.0.0:8000
    server_socket = socket.socket()
    server_socket.bind(('', 12397))
    server_socket.listen(0)

    # Accept a single connection and make a file-like object out of it
    conn = server_socket.accept()[0]
    connection = conn.makefile('rb')

    print('UIBBB: connected to client!')

    # initialize UI
    UIThread = user_interface.UserInterface()
    UIThread.start()

    try:
        main(conn)
    finally:
        connection.close()
        UIThread.kill()
        server_socket.close()
