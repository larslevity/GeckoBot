
""""Supplies controllers and utilities for controllers
"""
import abc
import numpy as np  # pragma: no cover


# pylint: disable=too-few-public-methods
class Controller(object):  # pragma: no cover
    """Base class for controllers. This defines the interface to controllers"""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def reset_state(self):
        """
        Reset the states of the controller to zero
        """

    @abc.abstractmethod
    def set_maxoutput(self):
        """
        Set the maximal output of the Controller
        """

    @abc.abstractmethod
    def output(self, reference, system_output):
        """ compute the controller output and return

        Args:
            reference (float): where the system should be
            system_output (float): where the system actually is

        Returns:
            (float): controller_output for given input data
        """
        return


class PController(Controller):
    """A simple proportional controller"""

    def __init__(self, proportional, max_output):
        """
        Args:
            proportional (float): proportional gain of the P-Ctr
            max_output (float): some upper limit for the output
        """
        self.proportional = proportional
        self.max_output = max_output

    def output(self, reference, system_output):
        """
        Returns:
            (float): proportinal*(reference-sytem_output)
        """
        controller_output = -self.proportional*(system_output-reference)

        if abs(controller_output) > self.max_output:
            # return math.copysign(self.max_output, controller_output)
            controller_output = np.sign(controller_output) * self.max_output
        return controller_output

    def set_initial_cable_length(self, set_initial_cable_length):
        pass

    def reset_state(self):
        pass


class PidController(Controller):
    """
    A simple PID controller
    """
    def __init__(self, gain, tsampling, max_output):
        """
        Args:
            gain (list): gains of the diffrent parts of ctr

                ====== = ============
                | gain = [Kp, Ti, Td]
                ====== = ============

            Ts (float): sampling time of the controller / overall system
            max_output (float): saturation of output

        Example:
            >>> Kp, Ti, Td = 10, 1.2, .4
            >>> gain = [Kp, Ti, Td]
            >>> tsampling, max_output = .001, 100
            >>> controller = PidController(gain, tsampling, max_output)
        """
        # Tuning Knobes
        self.Kp = gain[0]
        self.Ti = gain[1]
        self.Td = gain[2]
        self.max_output = max_output
        self.integral = 0.
        self.last_err = 0.
        self.last_out = 0.
        self.windup_guard = 0
        self.gam = .1   # pole for stability. Typically = .1
        self.tsampling = tsampling
        self.initial_cable_length = None

    def set_maxoutput(self, maxoutput):
        self.max_output = maxoutput

    def set_initial_cable_length(self, initial_cable_length):
        self.initial_cable_length = initial_cable_length

    def reset_state(self):
        self.integral = 0.
        self.last_err = 0.
        self.windup_guard = 0.
        self.last_out = 0.

    def set_gain(self, gain):
        self.Kp = gain[0]
        self.Ti = gain[1]
        self.Td = gain[2]
        self.reset_state()

    def output(self, reference, system_output):
        """
        The controller output is calculated by:

        ========== = ======================================
        | e        = r-y
        |
        | ctr_out  = Kp*e + Kp/Ti*integral(e) + Kp*Td*de/dt
        ========== = ======================================

        Args:
            reference (float): where the system should be
            system_output (float): where the system actually is

        Returns:
            (float): controller_output
        """
        # calc error
        err = reference - system_output
        # Derivative Anteil
        # diff = (err - self.last_err)/self.tsampling
        diff = (self.gam*self.Td - self.tsampling/2) / \
            (self.gam*self.Td + self.tsampling/2) * \
            self.last_out + \
            self.Td/(self.gam+self.tsampling/2)*(err-self.last_err)
        self.last_err = err
        # Integral Anteil
        integ = self.integral + self.tsampling / \
            (2*self.Ti)*(err-self.windup_guard)
        if np.abs(integ) > self.max_output:
            integ = self.max_output*np.sign(integ)
        self.integral = integ

        # Sum
        controller_output = self.Kp*(err + integ + diff)

        if np.abs(controller_output) > self.max_output:
            self.windup_guard = controller_output * \
                (1-self.max_output/abs(controller_output))
            self.last_out = self.max_output*np.sign(controller_output)
        else:
            self.windup_guard = 0
            self.last_out = controller_output
        return self.last_out


class PidController_WindUp(Controller):
    """
    A simple PID controller
    """
    def __init__(self, gain, tsampling, max_output):
        """
        Args:
            gain (list): gains of the diffrent parts of ctr

                ====== = ============
                | gain = [Kp, Ti, Td]
                ====== = ============

            Ts (float): sampling time of the controller / overall system
            max_output (float): saturation of output

        Example:
            >>> Kp, Ti, Td = 10, 1.2, .4
            >>> gain = [Kp, Ti, Td]
            >>> tsampling, max_output = .001, 100
            >>> controller = PidController(gain, tsampling, max_output)
        """
        # Tuning Knobes
        self.Kp = gain[0]
        self.Ti = gain[1]
        self.Td = gain[2]
        self.max_output = max_output
        self.integral = 0.
        self.last_err = 0.
        self.last_out = 0.
        self.windup_guard = 0
        self.gam = .1   # pole for stability. Typically = .1
        self.tsampling = tsampling
        self.initial_cable_length = None

    def set_maxoutput(self, maxoutput):
        self.max_output = maxoutput

    def set_initial_cable_length(self, initial_cable_length):
        self.initial_cable_length = initial_cable_length

    def reset_state(self):
        self.integral = 0.
        self.last_err = 0.
        self.windup_guard = 0.
        self.last_out = 0.

    def set_gain(self, gain):
        self.Kp = gain[0]
        self.Ti = gain[1]
        self.Td = gain[2]
        self.reset_state()

    def output(self, reference, system_output):
        """
        The controller output is calculated by:

        ========== = ======================================
        | e        = r-y
        |
        | ctr_out  = Kp*e + Kp/Ti*integral(e) + Kp*Td*de/dt
        ========== = ======================================

        Args:
            reference (float): where the system should be
            system_output (float): where the system actually is

        Returns:
            (float): controller_output
        """
        # calc error
        err = reference - system_output
        # Derivative Anteil
        # diff = (err - self.last_err)/self.tsampling
        diff = (self.gam*self.Td - self.tsampling/2) / \
            (self.gam*self.Td + self.tsampling/2) * \
            self.last_out + \
            self.Td/(self.gam+self.tsampling/2)*(err-self.last_err)
        self.last_err = err
        # Integral Anteil
        integ = self.integral + self.tsampling / (2*self.Ti)*(err)
        self.integral = integ

        # Sum
        controller_output = self.Kp*(err + integ + diff)

        if np.abs(controller_output) > self.max_output:
            self.last_out = self.max_output*np.sign(controller_output)
        else:
            self.last_out = controller_output
        return self.last_out


class PidController_SymPy(Controller):
    """
    A simple PID controller
    """
    def __init__(self, gain, tsampling, max_output):
        """
        Args:
            gain (list): gains of the diffrent parts of ctr

                ====== = ============
                | gain = [Kp, Ti, Td]
                ====== = ============

            Ts (float): sampling time of the controller / overall system
            max_output (float): saturation of output

        Example:
            >>> Kp, Ti, Td = 10, 1.2, .4
            >>> gain = [Kp, Ti, Td]
            >>> tsampling, max_output = .001, 100
            >>> controller = PidController(gain, tsampling, max_output)
        """
        self.max_output = max_output
        self.err2 = 0.
        self.err1 = 0.
        self.out2 = 0.
        self.out1 = 0.
        self.i_term1 = 0.
        self.gam = .1   # pole for stability. Typically = .1
        self.windup_guard = 0
        self.tsampling = tsampling
        self.set_gain(gain)

    def set_maxoutput(self, maxoutput):
        self.max_output = maxoutput

    def reset_state(self):
        self.err2 = 0.
        self.err1 = 0.
        self.out2 = 0.
        self.out1 = 0.
        self.i_term1 = 0.

    def set_gain(self, gain):
        self.Ti = gain[1]
        self.Kp = gain[0]
        Kp = gain[0]
        Ti = gain[1]
        Td = gain[2]
        Ts = self.tsampling
        gam = self.gam
        self.k0 = (4*Td*Ti*gam - 2*Ti*Ts)/(4*Td*Ti*gam + 2*Ti*Ts)
        self.k1 = -8*Td*Ti*gam/(4*Td*Ti*gam + 2*Ti*Ts)
        self.k2 = (4*Kp*Td*Ti*gam + 4*Kp*Td*Ti - 2*Kp*Td*Ts*gam -
                   2*Kp*Ti*Ts + Kp*Ts**2)/(4*Td*Ti*gam + 2*Ti*Ts)
        self.k3 = (-8*Kp*Td*Ti*gam - 8*Kp*Td*Ti + 2*Kp*Ts**2) / \
                  (4*Td*Ti*gam + 2*Ti*Ts)
        self.k4 = (4*Kp*Td*Ti*gam + 4*Kp*Td*Ti + 2*Kp*Td*Ts*gam + 2*Kp*Ti*Ts +
                   Kp*Ts**2)/(4*Td*Ti*gam + 2*Ti*Ts)
        self.ky1 = (-2*Td*gam + Ts)/(2*Td*gam + Ts)
        self.ke1 = -(2*Kp*Td*gam + 2*Kp*Td - Kp*Ts)/(2*Td*gam + Ts)
        self.ke0 = (2*Kp*Td*gam + 2*Kp*Td + Kp*Ts)/(2*Td*gam + Ts)
        self.kdy1 = (-2*Td*gam + Ts)/(2*Td*gam + Ts)
        self.kde1 = -2*Td/(2*Td*gam + Ts)
        self.kde0 = 2*Td/(2*Td*gam + Ts)
        self.reset_state()

    def output(self, reference, system_output):
        """
        The controller output is calculated by:

        ========== = ======================================
        | e        = r-y
        |
        | ctr_out  = Kp*e + Kp/Ti*integral(e) + Kp*Td*de/dt
        ========== = ======================================

        Args:
            reference (float): where the system should be
            system_output (float): where the system actually is

        Returns:
            (float): controller_output
        """
        # calc error
        err0 = reference - system_output
        d_term = -self.kdy1*self.out1 + self.kde1*self.err1 + self.kde0*err0

        # pd_term = -self.ky1*self.out1 + self.ke1*self.err1 + self.ke0*err0
        i_term = self.i_term1 + self.tsampling/(2*self.Ti)*(self.err1 + err0 -
                                                            self.windup_guard)
        if np.abs(i_term) > self.max_output:
            i_term = self.max_output*np.sign(i_term)
        self.i_term1 = i_term
        self.err1 = err0
        out = self.Kp*(err0 + d_term + i_term)

#        out = -self.k0*self.out2 - self.k1*self.out1 + self.k2*self.err2 \
#            + self.k3*self.err1 + self.k4*err
#        self.out2 = self.out1
#        self.err2 = self.err1
#        self.err1 = err

        if np.abs(out) > self.max_output:
            self.out1 = self.max_output*np.sign(out)
            self.windup_guard = out*(1-self.max_output/abs(out))
        else:
            self.out1 = out
            self.windup_guard = 0
        return self.out1


def sys_input(ctr_out):
    return (.5 + ctr_out/2)*100
