
""" Main function running on BBB """
from __future__ import print_function

import sys
import time
import logging
import errno

from socket import error as SocketError
import threading


from Src.Management import timeout
from Src.Management import exception
from Src.Communication import user_interface as HUI

from Src.Visual.PiCamera import client
from Src.Management import load_pattern as ptrn


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
            rootLogger.info("Try to start server ...")
            if IMGPROC:
                client.start_img_processing(RPi_ip)
                time.sleep(10)
                imgprocsock = client.IMGProcSocket(RPi_ip)
                rootLogger.info("RPi Server found: Img Processing is running")
            else:
                client.start_server(RPi_ip)
                time.sleep(3)
                camerasock = client.ClientSocket(RPi_ip)
                rootLogger.info("RPi Server found: MakeImageServer is running")
        except exception.TimeoutError:
            rootLogger.info("Server not found")
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
            rootLogger.info("Connected to LivePlot Server")
        except exception.TimeoutError:
            rootLogger.info("Live Plot Server not found")
        except SocketError as err:
            if err.errno == errno.ECONNREFUSED:
                rootLogger.info("LivePlotter Server refused connection")
            elif err.errno == errno.EADDRINUSE:
                rootLogger.info("LivePlotter Server already in Use")
            else:
                raise

    return camerasock, imgprocsock, plotsock



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
    class SharedMemory(object):
        """ Data, which is shared between Threads """
        def __init__(self):
            self.sampling_time = TSAMPLING

            

            self.xref = (None, None)
            self.rec_aIMG = {name: None for name in CHANNELset}
            self.rec_X = {name: None for name in range(8)}  # 6 markers
            self.rec_Y = {name: None for name in range(8)}
            self.rec_eps = None

            self.rec_aIMU = {name: None for name in CHANNELset}

            self.ptrndic = {
                name: ptrn.read_list_from_csv('Patterns/'+name)
                for name in ptrn.get_csv_files()}
            self.ptrndic['selected'] = sorted(list(self.ptrndic.keys()))[0]
            self.pattern = self.ptrndic[self.ptrndic['selected']]

    rootLogger.info('Initialize Hardware ...')
    PSens, PValve, DValve, IMU, Ctr, ImuCtr = init_channels()

    rootLogger.info('Initialize the shared variables, i.e. cargo ...')
    shared_memory = SharedMemory()


    """ ---------------- ----- ------- ------------------------- """
    """ ---------------- State Handler ------------------------- """
    """ ---------------- ----- ------- ------------------------- """



    rootLogger.info('Starting Communication Thread ...')
    communication_thread = HUI.HUIThread(shared_memory, rootLogger)
    communication_thread.setDaemon(True)
    communication_thread.start()

    camerasock, imgprocsock, plotsock = init_server_connections()
    communication_thread.set_camera_socket(camerasock)

    if imgprocsock:
        camReader = CameraReader(shared_memory, imgprocsock)
        camReader.setDaemon(True)
        camReader.start()
        rootLogger.info('Started the CamReader Thread')
    if PRINTSTATE:
        IMG = True if imgprocsock else False
        printer_thread = HUI.Printer(shared_memory, plotsock, IMU, IMG)
        printer_thread.setDaemon(True)
        printer_thread.start()
        rootLogger.info('Started the Printer Thread')

    try:
        rootLogger.info('Run the StateMachine ...')
        automat.run(shared_memory)
    except KeyboardInterrupt:
        rootLogger.exception('keyboard interrupt detected...   killing UI')

    except Exception as err:
        rootLogger.exception(
            '\n----------caught exception! in Main Thread----------------\n')
        rootLogger.exception("Unexpected error:\n", sys.exc_info()[0])
        rootLogger.exception(sys.exc_info()[1])
        rootLogger.error(err, exc_info=True)
        rootLogger.info('\n ----------------------- killing UI --')
    finally:
        if PRINTSTATE:
            printer_thread.kill()
        if imgprocsock:
            imgprocsock.close()
            camReader.kill()
        if camerasock:
            camerasock.close()
        if plotsock:
            plotsock.close()
        communication_thread.kill()

    communication_thread.join()
    if PRINTSTATE:
        printer_thread.join()
    rootLogger.info('All is done ...')
    sys.exit(0)


class CameraReader(threading.Thread):
    def __init__(self, shared_memory, imgprocsock):
        threading.Thread.__init__(self)
        self.shared_memory = shared_memory
        self.is_running = True
        self.imgprocsock = imgprocsock

    def run(self):
        while self.is_running:
            alpha, eps, (X, Y), xref = self.imgprocsock.get_alpha()
            alpha = alpha + [None, None]
            X = X + [None, None]
            Y = Y + [None, None]
            for i in range(8):
                self.shared_memory.rec_X[i] = X[i]
                self.shared_memory.rec_Y[i] = Y[i]
                self.shared_memory.rec_aIMG[i] = alpha[i]

            self.shared_memory.rec_eps = eps
            self.shared_memory.xref = xref

    def kill(self):
        self.is_running = False


if __name__ == '__main__':
    main()
