# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 13:43:02 2017
@author: ls
ref:
https://docs.python.org/2/library/pickle.html#data-stream-format
"""

import pickle


def pickle_data(data):
    """
        returns a string repr of data (if its pickable)
    """
    return pickle.dumps(data)


def unpickle_data(string):
    """
        returns the data of the string repr
    """
    return pickle.loads(string)
