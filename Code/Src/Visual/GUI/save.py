# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 16:32:12 2016

@author: ls

requirements:
pip install deepdish

http://deepdish.io/2014/11/11/python-dictionary-to-hdf5/
"""

try:
    import deepdish
except ImportError:
    print('Can not import Deepdish')
import matplotlib.pyplot as plt
from matplotlib2tikz import save as tikz_save
import fileinput
import csv
import numpy as np
import os
from time import strftime


def save_recorded_data(data, filename):
    """ save the recorded data from GlobalData object to .h5 file  """
    deepdish.io.save(filename, data)


def save_recorded_data_as_csv(data, filename=None, StartStop=None):
    if not filename:
        exp = 'exp--'
        filename = exp+strftime("%Y_%m_%d__%H_%M_%S")+'.csv'
    dirname = os.path.dirname(os.path.realpath(__file__))
    realpath = '../../../../../GeckoBotExperiments/current_exp/' + filename
    filename = os.path.join(dirname, realpath)
    filename = os.path.abspath(os.path.realpath(filename))
 
    if StartStop:
        start, stop = StartStop
    else:
        start, stop = [0, data.max_idx]
    d = {key: data[key]['val'][start:stop] for key in data}
    keys = sorted(d.keys())
    with open(filename, "wb") as outfile:
        writer = csv.writer(outfile, delimiter="\t")
        writer.writerow(keys)
        writer.writerows(zip(*[d[key] for key in keys]))


def read_csv(filename):
    dic = {}
    mapping = {}
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        for idx, row in enumerate(reader):
            # print ', '.join(row)
            if idx == 0:
                for jdx, key in enumerate(row):
                    mapping[jdx] = key
                    dic[key] = []
            else:
                for jdx, val in enumerate(row):
                    dic[mapping[jdx]].append(float(val) if val else np.nan)
    return dic


def save_current_plot_as_tikz(toplevel, filename):
    print('Saving as TikZ-Picture...')
    plot_win = toplevel.analyse_win.plot_win
    keylist = toplevel.analyse_win.select_win.keylist

    plt.figure()
    # get selection
    for artist, elem in enumerate(keylist):
        ord_val = plot_win.getdata(elem[1])
        abs_val = plot_win.getdata(elem[0])
        # update line
        label = elem[0] + '-' + elem[1]
        label = label.replace('_', '\\_')
        plt.plot(abs_val, ord_val, label=label)

    plt.legend()
    plt.grid()
    # print(filename)
    tikz_save(filename)
    insert_tex_header(filename)
    print('Done!')


def load_data(filename):
    """ Reading data back """
    return_data = deepdish.io.load(filename)
    return return_data


def insert_tex_header(filename):
    header = \
        "\\documentclass[crop,tikz]{standalone} \
         \\usepackage[utf8]{inputenc} \
         \\usepackage{tikz} \
         \\usepackage{pgfplots} \
         \\pgfplotsset{compat=newest} \
         \\usepgfplotslibrary{groupplots} \
         \\begin{document} \
         "
    line_pre_adder(filename, header)
    # Append Ending
    ending = "%% End matplotlib2tikz content %% \n \\end{document}"
    with open(filename, "a") as myfile:
        myfile.write(ending)


def line_pre_adder(filename, line_to_prepend):
    f = fileinput.input(filename, inplace=1)
    for xline in f:
        if f.isfirstline():
            print(line_to_prepend.rstrip('\r\n') + '\n' + xline,)
        else:
            print(xline,)
