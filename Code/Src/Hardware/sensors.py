# pylint: skip-file

"""Sensor classes to interface with hardware"""
try:
    import Adafruit_BBIO.ADC as ADC
except ImportError:
    print "Can't import Adafruit_BBIO.ADC"

try:
    import Adafruit_GPIO.I2C as Adafruit_I2C
except ImportError:
    print "Can't import Adafruit_I2C"

import subprocess


# import random

# Auf "P9_25" liegt eine Schwingung, funktioniert nicht.


class PressureSens(object):
    def __init__(self, name, pin_0):
        """
        Software Representation of a Pressure Sensor (MPX2200AP)

        1.8V is the maximum voltage. Do not exceed 1.8V on the AIN pins !!
        VDD_ADC (P9_32) provides 1.8V. Use GNDA_ADC (P9_34) as the ground.

        ref:
        http://forum.arduino.cc/index.php?topic=281908.0
        https://learn.adafruit.com/setting-up-io-python-library-on-beaglebone-black/adc

        Valid ADC Pins:
            AIN0 - P9_39
            AIN1 - P9_40
            AIN2 - P9_37
            AIN3 - P9_38
            AIN4 - P9_33
            AIN5 - P9_36
            AIN6 - P9_35

        *Initialize with*

        Args:
            name (str): The name of the sensor
            pin_0 (str): Input pin 0 for PressureSens
        """
        ADC.setup()
        self.PinVPlus = pin_0
#        self.PinVMin = pin_1
        self.offset = 0.0  # to calibrate the sensor
        self.name = name

    def get_value(self):
        """
        Returns the actual pressure value of pressure Sens.
        0.2mV per kPa at 10V.
        Since the 'diff' is a float in volt,
        the pressure is 1/0.2mV times the diff.
        So if the voltage changes 1 mV the pressure changes 5 kPa.

        Returns:
            pressure (float): the measured pressure
        """
#        vPlus = ADC.read(self.PinVPlus) * 1.8  # in [V]
#        vMin = ADC.read(self.PinVMin) * 1.8  # in [V]
#
#        diff = vPlus - vMin
#        diff -= self.offset
#        pressure = diff  # / 0.0002  # 0.0002V is 0.2mV

        values = []
        for i in range(10):
            values.append(ADC.read(self.PinVPlus))
        values = values[2:]  # delete the first tweo entries
        voltage = sum(values)/float(len(values)) * 1.8  # Volt
        pressure = voltage  # * 5
        return pressure


def i2cdetect():
    bashCommand = "i2cdetect -y -r 2"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    print(error)


class MultiPlexer(object):
    def __init__(self, address=0x70):
        self.i2c = Adafruit_I2C.get_i2c_device(address, busnum=2)

    def select(self, port_id):
        self.i2c.write8(0, 1 << port_id)


class DPressureSens(object):
    plexer = MultiPlexer()

    def __init__(self, name, mplx_id, address=0x28, maxpressure=1):
        self.mplx_id = mplx_id
        self.i2c = Adafruit_I2C.get_i2c_device(address, busnum=2)
        self.name = name
        self.maxpressure = maxpressure

        self.pmin = 0.0
        self.pmax = 150.0
        self.outmin = (2**14-1)*.1
        self.outmax = (2**14-1)*.9

    def calc_pressure(self, msb, lsb):
        output = msb*256 + lsb
        pressure = (output-self.outmin)*(self.pmax-self.pmin)/(
            self.outmax - self.outmin) + self.pmin
        pressure = pressure/14.5038  # [bar]
        return pressure

    def get_value(self):
        self.plexer.select(self.mplx_id)
        sens_bytes = self.i2c.readList(register=0, length=2)
        msb = sens_bytes[0]
        lsb = sens_bytes[1]
        pressure = self.calc_pressure(msb, lsb)
        return pressure/self.maxpressure

    def set_maxpressure(self, maxpressure):
        self.maxpressure = maxpressure
