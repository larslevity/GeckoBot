""" Tests for control utilities"""

import unittest
# from nose.plugins.attrib import attr
from Src.Controller import controller
# http://code.tutsplus.com/tutorials/beginning-test-driven-development-in-python--net-30137
# http://nose.readthedocs.org/en/latest/plugins/attrib.html
import control
import numpy as np


# pylint: disable=R0904
class TestPController(unittest.TestCase):
    """ Tests for controllers"""

    def setUp(self):
        gain_p = 10
        maxoutput = 100
        self.p_controller = controller.PController(gain_p, maxoutput)

    def test_p_controller_update(self):
        """Check output with and without saturation"""
        self.assertEqual(self.p_controller.output(10, 1), 90)
        self.assertEqual(self.p_controller.output(10, 19), -90)
        self.assertEqual(self.p_controller.output(10, -2), 100)
        self.assertEqual(self.p_controller.output(10, 22), -100)


class TestPidController(unittest.TestCase):
    """ Tests for controllers"""

    def setUp(self):
        gain_p = 1
        gain_i = 1
        gain_d = 1
        maxoutput = 100
        tsampling = .015
        self.pid_controller =\
            controller.PidController([gain_p, gain_i, gain_d],
                                     tsampling, maxoutput)

    def test_pid_controller_update(self):
        """Check output with and without saturation"""
        # without saturation
        ref = 2
        sys_out = 1
        self.assertLessEqual(
            abs(self.pid_controller.output(ref, sys_out)), 99)
        # with saturation
        ref = 1000
        self.assertEqual(
            self.pid_controller.output(ref, sys_out), 100)


class TestLqriController(unittest.TestCase):
    """ Tests for controllers"""

    def setUp(self):
        sysa = np.matrix([[0., 1., 0.],
                          [0., 0., 1.],
                          [0., -226.47015795, -5.15115767]])
        sysb = np.matrix([[0], [0], [1]])
        sysc = np.matrix([[0.48407208, 0., 0.]])
        sysd = 0
        sys = control.ss(sysa, sysb, sysc, sysd)
        weight_qi = 10
        weight_raug = 10
        weight_re = 1
        maxoutput = 100
        tsampling = .015
        self.lqri_controller =\
            controller.LqriController(sys, weight_qi, weight_raug, weight_re,
                                      tsampling, maxoutput)
        self.lqri_controller.set_initial_cable_length(1)

    def test_lqri_controller_update(self):
        """Check output with and without saturation"""
        # without saturation
        ref = 2
        sys_out = 1
        self.assertLessEqual(
            self.lqri_controller.output(ref, sys_out), 99)
        # with saturation
        ref = 10000
        self.assertEqual(
            abs(self.lqri_controller.output(ref, sys_out)), 100)
