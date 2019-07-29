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


def get_pattern_dir():
    dirname = path.dirname(path.realpath(__file__))
    realpath = '../../Patterns/'
    filename = path.join(dirname, realpath)
    base_dir = path.abspath(path.realpath(filename))
    return base_dir


def get_csv_files(rel_dir=''):
    search_dir = path.join(get_pattern_dir(), rel_dir)
    for entry in scandir(search_dir):
        if entry.is_file() and entry.name.endswith('.csv'):
            yield (entry.name, entry.path)


def get_dirs():
    pattern_dir = get_pattern_dir()
    for dir_ in scandir(pattern_dir):
        if dir_.is_dir():
            contain_csv = False
            for dir_entry in scandir(dir_.path):
                if dir_entry.is_file() and dir_entry.name.endswith('.csv'):
                    contain_csv = True
                    break
            if contain_csv:
                yield dir_.name


def get_pattern_dic():
    patterns = {}
    for dir_name in get_dirs():
        patterns[dir_name] = {}
        for csv_name, csv_path in get_csv_files(dir_name):
            patterns[dir_name][csv_name[:-4]] = read_list_from_csv(csv_path)
    return patterns


def get_clb_dic():
    clbs = {}
    for csv_name, csv_path in get_csv_files(dir_name):
        clbs[csv_name[:-4]] = read_list_from_csv(csv_path) 


if __name__ == '__main__':
    print('is main')
    __file__ = path.join(path.abspath(''), 'load_pattern.py')
    print(__file__)

    patterns = get_pattern_dic()
