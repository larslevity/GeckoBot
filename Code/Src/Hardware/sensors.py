# pylint: skip-file

"""Sensor classes to interface with hardware
To increase the speed of I2C:

https://randymxj.com/?p=538
https://groups.google.com/forum/#!topic/beagleboard/vbuM-4oShS8
"""

try:
    import Adafruit_GPIO.I2C as Adafruit_I2C
except ImportError:
    print("Can't import Adafruit_I2C")

import subprocess
import time


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
        self.outmin = int((2**14-1)*.1)
        self.outmax = int((2**14-1)*.9)
        self.clb = (self.pmax-self.pmin)/(self.outmax - self.outmin)
        self.barfact = 1/14.5038

    def calc_pressure(self, msb, lsb):
        output = msb*256 + lsb
        pressure = ((output-self.outmin)*self.clb + self.pmin)*self.barfact
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


class MPU_9150(object):
    plexer = MultiPlexer(address=0x71)

    def __init__(self, name, mplx_id, address=0x68):
        power_mgmt_1 = 0x6b     # register power management of IMU
        self.name = name
        self.mplx_id = mplx_id    # plex ID of IMU
        # MultiPlexer schlaten, um das Modul ansprechen zu koennen
        self.i2c = Adafruit_I2C.get_i2c_device(address, busnum=2)
        self.plexer.select(self.mplx_id)
        time.sleep(.1)
        # Power on of Acc
        self.i2c.write8(power_mgmt_1, 0x00)

    def _read_word(self, reg):
        sens_bytes = self.i2c.readList(register=reg, length=2)
        msb = sens_bytes[0]
        lsb = sens_bytes[1]
        value = (msb << 8) + lsb
        return value

    def _read_word_2c(self, reg):
        val = self._read_word(reg)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val

    def get_acceleration(self):
        self.plexer.select(self.mplx_id)

        acc_xout = self._read_word_2c(0x3b)
        acc_yout = self._read_word_2c(0x3d)
        acc_zout = self._read_word_2c(0x3f)
        return (acc_xout, acc_yout, acc_zout)


if __name__ == "__main__":
    IMU = MPU_9150(0)
    while True:
        x, y, z = IMU.get_acceleration()
        s = 'x_acc: {}\n'.format(x)
        s = s + 'y_acc: {}\n'.format(y)
        s = s + 'z_acc: {}\n'.format(z)
        print(s)
        time.sleep(.05)
