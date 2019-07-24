
""" Main function running on BBB """
from __future__ import print_function

import sys
import time
import logging
import errno

from socket import error as SocketError


from Src.Management import timeout
from Src.Management import exception

from Src.Visual.PiCamera import client
from Src.Controller import lowlevel_controller
from Src.Hardware import lcd as lcd_module
from Src.Hardware import user_interface as UI
from Src.Communication import printer


logPath = "log/"
fileName = 'testlog'
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


# ------------ CAMERA INIT

def init_server_connections(IMGPROC=True):
    camerasock, imgprocsock, plotsock = None, None, None
    RPi_ip = '134.28.136.49'
    pc_ip = '134.28.136.131'

    # RPi connection
    with timeout.timeout(12):
        try:
            if IMGPROC:
                client.start_img_processing(RPi_ip)
                time.sleep(10)
                imgprocsock = client.IMGProcSocket(RPi_ip)
                rootLogger.info("RPi Server found: Img Processing is running")
            else:
                client.start_server(RPi_ip)
                time.sleep(3)
                camerasock = client.ClientSocket(RPi_ip)
                rootLogger.info("RPi Server found: Camera is running")
        except exception.TimeoutError:
            rootLogger.info("RPi Server not found")
        except SocketError as err:
            if err.errno == errno.ECONNREFUSED:
                rootLogger.info("RPi Server refused connection")
            elif err.errno == errno.EADDRINUSE:
                rootLogger.info("RPi Server already in Use")
            else:
                raise
    # PC Dell Latitude Connection
    with timeout.timeout(2):
        try:
            plotsock = client.LivePlotterSocket(pc_ip)
            rootLogger.info("Connected to LivePlotter Server")
        except exception.TimeoutError:
            rootLogger.info("LivePlotter Server not found")
        except SocketError as err:
            if err.errno == errno.ECONNREFUSED:
                rootLogger.info("LivePlotter Server refused connection")
            elif err.errno == errno.EADDRINUSE:
                rootLogger.info("LivePlotter Server already in Use")
            else:
                raise

    return camerasock, imgprocsock, plotsock


class SystemConfig(object):
    def __init__(self):
        self.IMUsConnected = None
        self.Camera = None
        self.ImgProc = None
        self.LivePlotter = None
        self.ConsolePrinter = False

    def __str__(self):
        return ('System Configuration as follows:\n'
                + 'IMUs:\t\t {}connected\n'.format('' if self.IMUsConnected else 'not ')
                + 'Camera:\t\t {}connected\n'.format('' if self.Camera else 'not ')
                + 'ImgProc:\t {}connected\n'.format('' if self.ImgProc else 'not ')
                + 'LivePlotter:\t {}connected\n'.format('' if self.LivePlotter else 'not ')
                + 'ConsolePrinter:\t {}'.format('enabled' if self.ConsolePrinter else 'disabled')
                )


def main():
    """
    - Run the State Machine
        - switch between following states according to user or system given
          conditions:
            - PAUSE (do nothing but read sensors)
            - FEED_THROUGH (Set PWM direct from User Interface)
            - PRESSURE_REFERENCE (Use PSensCtr to track user-given reference)
            - ANGLE_REFERENCE (Use IMUCtr to track user-given reference)
            - EXIT (Cleaning..)
    - wait for communication thread to join
    """
    sys_config = SystemConfig()
    lcd = lcd_module.getlcd()

    try:

        rootLogger.info('Starting LowLevelController ...')
        lowlevelctr = lowlevel_controller.LowLevelController()
        lowlevelctr.start()
        time.sleep(.2)  # wait to init
        sys_config.IMUsConnected = lowlevelctr.is_imu_in_use()

        rootLogger.info('Searching for external devices in periphere...')
        camerasock, imgprocsock, plotsock = init_server_connections()
        sys_config.Camera = camerasock
        sys_config.ImgProc = imgprocsock
        sys_config.LivePlotter = plotsock

        rootLogger.info('Determinig System Configuartion ...')
        if not sys_config.LivePlotter:
            with timeout.timeout(3):
                try:
                    Q = 'Print States?'
                    ans = lcd.select_elem_from_list(['Yes', 'No '], Quest=Q)
                except exception.TimeoutError:
                    ans = 'No'
            sys_config.ConsolePrinter = True if ans == 'Yes' else False
        rootLogger.info(sys_config)

        rootLogger.info('Starting UserInterface ...')
        ui_thread = UI.UserInterface()
        ui_thread.setDaemon(True)
        ui_thread.start()

        if sys_config.ConsolePrinter:
            rootLogger.info('Starting Console Printer ...')
            cPrinter = printer.ConsolePrinter()
            cPrinter.setDaemon(True)
            cPrinter.start()

        if sys_config.LivePlotter:
            rootLogger.info('Starting GUI Printer ...')
            guiPrinter = printer.GUIPrinter(sys_config.LivePlotter,
                                            IMU=sys_config.IMUsConnected,
                                            IMG=sys_config.ImgProc)
            guiPrinter.setDaemon(True)
            guiPrinter.start()

        if sys_config.ImgProc:
            rootLogger.info('Starting Camera Reader ...')
            imgReader = client.ImgProcReader(imgprocsock)
            imgReader.setDaemon(True)
            imgReader.start()

        ui_thread.join()
        lowlevelctr.join()
        if sys_config.ConsolePrinter:
            cPrinter.join()
        if sys_config.LivePlotter:
            guiPrinter.join()
        if sys_config.ImgProc:
            imgReader.join()

    except KeyboardInterrupt:
        rootLogger.info('KeyboardInterrupt ...')

    finally:
        ui_thread.kill()
        lowlevelctr.kill()
        if sys_config.ConsolePrinter:
            cPrinter.kill()
        if sys_config.LivePlotter:
            guiPrinter.kill()
        if sys_config.ImgProc:
            imgReader.kill()

    rootLogger.info('All is done ...')
    lcd.display('Bye Bye')
    sys.exit(0)


if __name__ == '__main__':
    main()
