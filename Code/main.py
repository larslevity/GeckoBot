
""" Main function running on BBB """
from __future__ import print_function

import sys
import time
import logging
import errno

from socket import error as SocketError


from Src.Management import timeout
from Src.Management import exception


from Src.Controller import lowlevel_controller
from Src.Controller import highlevel_controller
from Src.Communication import printer
from Src.Communication import client
from Src.Management.thread_communication import sys_config


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

def init_ui_connections():
    ui_ip = '192.168.5.2'
    client.start_UI(ui_ip)
    time.sleep(3)
    ui_sock = client.UISocket(ui_ip)
    return ui_sock


def init_server_connections(IMGPROC=True):
    camerasock, imgprocsock, plotsock = None, None, None
    RPi_ip = '134.28.136.49'
    pc_ip = '134.28.136.131'
#    pc_ip = '192.168.7.1'

    # RPi connection
    with timeout.timeout(12):
        try:
            if IMGPROC:
                client.start_img_processing(RPi_ip)
                time.sleep(10)
                imgprocsock = client.IMGProcSocket(RPi_ip)
                rootLogger.info("RPi Server found: Img Processing is running")
            else:
                time.sleep(3)
#                client.start_image_capture_server(RPi_ip)
#                time.sleep(3)
#                camerasock = client.CameraSocket(RPi_ip)
#                rootLogger.info("RPi Server found: Camera is running")
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


def main():
    try:
        rootLogger.info('Initialize  UI Connection...')
        ui_sock = init_ui_connections()

        rootLogger.info('Asking for Camera or ImageProc ...')
        Q = 'Capture Images?'
        lis = ['Yes', 'No ']
        time_to_ans = 3
        ans = ui_sock.select_from_list(lis, Q, time_to_ans)
        IMGPROC = True if ans in [None, 'No'] else False

        rootLogger.info('Starting LowLevelController ...')
        lowlevelctr = lowlevel_controller.LowLevelController()
        lowlevelctr.start()
        time.sleep(.2)  # wait to init
        sys_config.IMUsConnected = lowlevelctr.is_imu_in_use()

        rootLogger.info('Searching for external devices in periphere...')
        camerasock, imgprocsock, plotsock = \
            init_server_connections(IMGPROC)
        sys_config.Camera = camerasock
        sys_config.ImgProc = imgprocsock
        sys_config.LivePlotter = plotsock
        sys_config.UI = ui_sock

        rootLogger.info('Determinig System Configuartion ...')
        if not sys_config.LivePlotter:
            Q = 'Print States?'
            lis = ['Yes', 'No ']
            time_to_ans = 2
            ans = ui_sock.select_from_list(lis, Q, time_to_ans)
            sys_config.ConsolePrinter = True if ans == 'Yes' else False
        rootLogger.info(sys_config)

        rootLogger.info('Starting HighLevelController ...')
        highlevelctr = highlevel_controller.HighLevelController()
        highlevelctr.setDaemon(True)
        highlevelctr.start()

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
            rootLogger.info('Starting ImgProc Reader ...')
            imgReader = client.ImgProcReader(sys_config.ImgProc)
            imgReader.setDaemon(True)
            imgReader.start()

#        if sys_config.Camera:
#            rootLogger.info('Starting Camera Trigger ...')
#            camTrigger = client.CameraTrigger(sys_config.Camera)
#            camTrigger.setDaemon(True)
#            camTrigger.start()

        rootLogger.info('Starting UserInterface ...')
        ui_thread = client.UIReader(ui_sock)
        ui_thread.run()


#        ui_thread.join()
        lowlevelctr.join()
        highlevelctr.join()
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
        highlevelctr.kill()
        if sys_config.ConsolePrinter:
            cPrinter.kill()
        if sys_config.LivePlotter:
            guiPrinter.kill()
        if sys_config.ImgProc:
            imgReader.kill()
        if sys_config.Camera:
            sys_config.Camera.close()

    rootLogger.info('All is done ...')
    sys.exit(0)


if __name__ == '__main__':
    main()
