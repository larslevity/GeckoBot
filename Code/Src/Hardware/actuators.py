# pylint: skip-file
import time
try:
    import Adafruit_BBIO.PWM as PWM
except ImportError:
    print "Can't import Adafruit_BBIO.PWM"

try:
    import Adafruit_BBIO.GPIO as GPIO
except ImportError:
    print "Can't import Adafruit_BBIO.GPIO"


from termcolor import colored

from Src.Management import exception


class Led(object):

    def __init__(self, pin_0):
        """*Initialize with*

        Args:
            pwm_pin_0 (str): Pin for pwm 1, e.g. "P8_18"
        """
        self.pin_0 = pin_0

    def set_led(self, state):
        """ Set the state of LED

        Args:
            state (int): 0 - off / 1 - on
        """
        if state is 0:
            print 'LED (at pin ', self.pin_0, ') is ', colored('off', 'red')
        elif state is 1:
            print 'LED (at pin ', self.pin_0, ') is ', colored('on', 'green')
        else:
            print 'state is not in [0, 1]'
        # TODO: implement as hardware


class Pump(object):
    """ Software Representation of the Pressure Pump
    """

    def __init__(self, pin_0):
        """*Initialize with*

        Args:
            pin_0 (str): Pin for discrete output, e.g. "P8_19"
        """
        self.pin = pin_0
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def test(self):
        for i in range(5):
            GPIO.output(self.pin, GPIO.HIGH)
            print 'PUMP (pin ', self.pin, ') is ', colored('HIGH', 'green')
            time.sleep(5)
            GPIO.output(self.pin, GPIO.LOW)
            print 'PUMP (pin ', self.pin, ') is ', colored('LOW', 'red')
            time.sleep(2)

    def set_pump(self, state):
        """ Set the state of the Pump
        """
        pass

    def release_pump(self):
        GPIO.cleanup()


class VacuumPump(object):
    """ Software Representation of the Vacuum Pump
    """

    def __init__(self, pin_0):
        """*Initialize with*

        Args:
            pin_0 (str): Pin for pwm 1, e.g. "P8_19"
        """
        self.pin = pin_0

    def set_pump(self, state):
        """ Set the state of the Pump
        """
        pass


class Valve(object):
    """ Software Representation of the Proportional Pressure Valve
    """

    def __init__(self, name, pwm_pin):
        """*Initialize with*

        Args:
           pwm_pin_0 (str): Pin for pwm 1, e.g. "P9_14"
        """
        self.name = name
        self.pwm_pin = pwm_pin

        print(
            'starting PWM with duty cycle 0 at Prportional Valve ', self.name)
        PWM.start(self.pwm_pin, 0, 25000)
        PWM.set_duty_cycle(self.pwm_pin, 0)

    def cleanup(self):
        """Stop pwm services."""
        print(
            'stop PWM duty cycle 0 Prportional Valve ', self.name)

        PWM.stop(self.pwm_pin)
        PWM.cleanup()

    def set_pwm(self, duty_cycle):
        """Set the pwm to **duty_cycle**

        Args:
            duty_cycle (int): Value between 0 to 100
        """
        PWM.set_duty_cycle(self.pwm_pin, duty_cycle)


class DiscreteValve(object):
    """ Software Representation of the Discrete Pressure Valve
    """

    def __init__(self, name, pin):
        """*Initialize with*

        Args:
           pin (str): Pin GPIO of BBB, e.g. "P8_7"
        """
        self.name = name
        self.pin = pin
        self.state = 0
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def set_state(self, state):
        if self.state != state:
            if int(state) == 1:
                GPIO.output(self.pin, GPIO.HIGH)
                self.state = state
            elif int(state) == 0:
                GPIO.output(self.pin, GPIO.LOW)
                self.state = state
            else:
                raise exception.ArgumentError(
                    'set_state(state) needs either 1 or 0.\
                     Or accordings Booleans')

    def cleanup(self):
        GPIO.cleanup()
