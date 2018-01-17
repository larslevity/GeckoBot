# -*- coding: utf-8 -*-
"""
Created on Sun May 29 12:29:56 2016

@author: ls

refered to:
http://www.python-course.eu/finite_state_machine.php
"""
# pylint: disable=bare-except


from Src.Management import exception


class StateMachine(object):
    """ A simple code snippet that represents a state machine in python """
    def __init__(self):
        self.handlers = {}
        self.start_state = None
        self.end_states = []

    def add_state(self, name, handler, end_state=False):
        """ Adds an state to the state machine.

        Args:
            - name (str): the name of the state
            - handler (callable): a function(cargo) that defines what happens
                in this state. This function should return the next_state and
                cargo, where cargo is something which is transported from state
                to state.
            - end_state (Optional bool): Defines if added state is end_state
        """
        name = name.upper()
        self.handlers[name] = handler
        if end_state:
            self.end_states.append(name)

    def set_start(self, name):
        """
        Args:
            - name (str): Set an already added state to start_state
        """
        self.start_state = name.upper()

    def run(self, cargo):
        """
        Run the Automaton.

        Args:
            - cargo (object): the things that are manipulating the statemachine
        """
        try:
            handler = self.handlers[self.start_state]
        except:
            raise exception.InitializationError(
                "must call .set_start() before .run()")
        if not self.end_states:
            raise exception.InitializationError(
                "at least 1 state must be an end_state")

        while True:
            (new_state, cargo) = handler(cargo)
            if new_state.upper() in self.end_states:
                print("reached ", new_state)
                break
            else:
                handler = self.handlers[new_state.upper()]
