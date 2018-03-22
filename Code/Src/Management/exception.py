# -*- coding: utf-8 -*-
"""
Created on Wed Jun  1 16:34:11 2016

@author: ls
"""


class NotInWorkspaceError(Exception):
    """ Raised if the tuple that is to be appended does not lie in the
    workspace. """
    def __init__(self, value):
        super(NotInWorkspaceError, self).__init__()
        self.value = value

    def __str__(self):
        """ The string representation of this Exception """
        return repr(self.value)


class InitializationError(Exception):
    """ Is Raised when StateMachine.run() is called before initialization is
    completed correctly """
    def __init__(self, value):
        super(InitializationError, self).__init__()
        self.value = value

    def __str__(self):
        """ The string representation of the value of the InitializationError
        """
        return repr(self.value)


class TimeoutError(Exception):
    def __init__(self, value):
        super(TimeoutError, self).__init__()
        self.value = value

    def __str__(self):
        """ The string representation of the value of the InitializationError
        """
        return repr(self.value)


class ArgumentError(Exception):
    def __init__(self, value):
        super(ArgumentError, self).__init__()
        self.value = value

    def __str__(self):
        """ The string representation of the value of the ArgumentError
        """
        return repr(self.value)

