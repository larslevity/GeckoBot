#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  5 17:49:59 2019

@author: mustapha
"""
try:
    from os import scandir
except ImportError:
    from scandir import scandir
import csv
from os import path


def save_list_as_csv(lis, filename='test.csv'):
    # with open(filename, 'w', newline='') as f:
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(lis)


def read_list_from_csv(filename):
    out = []
    with open(filename) as f:
        reader = csv.reader(f)
        for row in reader:
            line = []
            for val in row:
                if val == 'True':
                    line.append(True)
                elif val == 'False':
                    line.append(False)
                else:
                    try:
                        line.append(float(val))
                    except ValueError:
                        line.append(val)
            out.append(line)
    return out


def get_local_dir():
    dirname = path.dirname(path.realpath(__file__))
    realpath = '../../Patterns/'
    filename = path.join(dirname, realpath)
    base_dir = path.abspath(path.realpath(filename))
    return base_dir


def get_csv_files():
    for entry in scandir(get_local_dir()):
        if entry.is_file() and entry.name.endswith('.csv'):
            yield entry.name
        else:
            print('No *.csv available')
