# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 14:36:51 2017

@author: ls
"""

import socket
import sys

from Src.Management import timeout
from Src.Communication import pickler


def update_sensors(sock, only_sens=True):
    order = [['update']]
    send_all(sock, order)
    sens_data, rec_u, rec_r = recieve_data(sock)
    if only_sens:
        return sens_data
    else:
        return sens_data, rec_u, rec_r


def change_state(sock, new_state):
    candidates = ['PAUSE', 'REFERENCE_TRACKING', 'EXIT',
                  'USER_CONTROL', 'USER_REFERENCE']
    order = [['change_state', new_state]]
    ans = None
    while ans not in candidates:
        send_all(sock, order)
        ans = recieve_data(sock)
    return ans


def set_valve(valve_data, order=[]):
    order.append(['set_valve', valve_data])
    return order


def set_ref(ref_data, order=[]):
    order.append(['set_ref', ref_data])
    return order


def set_dvalve(dvalve_data, order=[]):
    order.append(['set_dvalve', dvalve_data])
    return order


def send_all(sock, order):
    sock.sendall(pickler.pickle_data(order))


def recieve_data(sock):
    ans = pickler.unpickle_data(sock.recv(4096))
    return ans


def set_PID_gain(sock, ctr_id, gain_data):
    order = [['set_pidgain', ctr_id, gain_data]]
    send_all(sock, order)
    ans = recieve_data(sock)
    print('sent set_PID_gain', ctr_id, '. value:', gain_data, 'ans=', ans)


def set_maxpressure(sock, maxpressure):
    order = [['set_maxpressure', maxpressure]]
    send_all(sock, order)
    ans = recieve_data(sock)
    print('sent set_maxpressure', maxpressure, 'ans=', ans)


def set_maxctrout(sock, maxctrout):
    order = [['set_maxctrout', maxctrout]]
    send_all(sock, order)
    ans = recieve_data(sock)
    print('sent set_maxctrout', maxctrout, 'ans=', ans)


def set_tsampling(sock, tsampling):
    order = [['set_tsampling', tsampling]]
    send_all(sock, order)
    ans = recieve_data(sock)
    print('sent set_tsampling', tsampling, 'ans=', ans)


def set_pattern(sock, pattern):
    order = [['set_pattern', pattern]]
    print('sending set_pattern...')
    send_all(sock, order)
    ans = recieve_data(sock)
    print('sent set_pattern', pattern, 'ans=', ans)


def set_walking_state(sock, state):
    order = [['set_walking', state]]
    send_all(sock, order)
    ans = recieve_data(sock)
    print('sent set_walking', state, 'ans=', ans)


def get_meta_data(sock):
    """ Get informations about initialized things at the BBB
    """
    sens_data, rec_u, rec_r = update_sensors(sock, only_sens=False)

    order = [['valve_meta_info']]
    send_all(sock, order)
    valve_data, max_pressure, max_ctrout, tsampling, PID_gains, pattern = \
        recieve_data(sock)

    order = [['dvalve_meta_info']]
    send_all(sock, order)
    dvalve_data = recieve_data(sock)

    return (sens_data, rec_u, rec_r, valve_data, dvalve_data, max_pressure,
            max_ctrout, tsampling, PID_gains, pattern)


def init_BBB_connection(hostname):
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    # eth0 IP of BBB in AmP: 134.28.136.51
    hostname = '192.168.7.2'  # static IP of BBB-USB
    server_address = (hostname, 10000)
    print >>sys.stderr, 'connecting to %s port %s' % server_address
    with timeout.timeout():
        sock.connect(server_address)
    return sock
