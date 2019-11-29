# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 13:43:02 2017
@author: ls
ref:
https://docs.python.org/2/library/pickle.html#data-stream-format
"""

import pickle
import sys

if sys.version_info > (3, 0):
    def unpickle_data(string):
        return pickle.loads(string, encoding='latin1')
else:
    def unpickle_data(string):
        return pickle.loads(string)


def pickle_data(data):
    """
        returns a string repr of data (if its pickable)
    """
    return pickle.dumps(data, protocol=2)
