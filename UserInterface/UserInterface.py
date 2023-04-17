import cv2  # pip install opencv-python
# pip install pysimplegui (https://realpython.com/pysimplegui-python/)
import PySimpleGUI as sg
import numpy as np
import logging
import threading
import time
import queue

# Index of the camera to use.
CAMERA_INDEX = 0
# Global window reference.
sg.theme("DarkBlack")

# UI Layout
left_column = [
    [sg.Button("Calibrate", size=(20, 1), key="-CALIBRATE-")],
    [sg.Multiline("", size=(100, 50), key="-LOG-", disabled=True)],
    [sg.Button("Exit", size=(10, 1), key="-EXIT-")],
]
right_column = [
    [sg.Image(filename="", key="-CAMERA_IMAGE-", size=(1000, 800))],
    [sg.Checkbox(key="-CHECK_BOX_HSV_ONLY-", text="HSV only",
                 default=False, enable_events=True)]
]
layout = [
    [
        sg.Column(left_column),
        sg.VSeperator(),
        sg.Column(right_column)
    ]
]
# Window reference
g_window = sg.Window("Rockey Hockey", layout, resizable=True, finalize=True)

logger = logging.getLogger('RockeyHockey')

# Multithreaded logger: https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Multithreaded_Logging.py


def externalFunction():
    logger.info('Hello from external app')
    logger.info('External app sleeping 5 seconds')
    time.sleep(5)
    logger.info('External app waking up and exiting')

# Base class for everything called from the UI so the UI does not freeze.


class ThreadedAction(threading.Thread):
    def __init__(self, function):
        super().__init__()
        self._stop_event = threading.Event()
        # Function to run when .start() is called.
        self._function = function
        # if args.count() == 0:
        #     self._args = None
        # if kwargs == None:
        #     self._kwargs = None

    # def __init__(self, function, *args, **kwargs):
    #     super().__init__()
    #     self._stop_event = threading.Event()
    #     # Function to run when .start() is called.
    #     self._function = function
    #     self._args = args
    #     self._kwargs = kwargs

    def run(self):
        self._function()
        # externalFunction()
        # if self._args == None and self._kwargs == None:
        #     self._function()
        # else:
        #     self._function(self._args, self._kwargs)

    def stop(self):
        self._stop_event.set()


class ThreadedActionArgs(threading.Thread):
    def __init__(self, function, *args):
        super().__init__()
        self._stop_event = threading.Event()
        # Function to run when .start() is called.
        self._function = function
        self._args = args

    def run(self):
        self._function(self._args)

    def stop(self):
        self._stop_event.set()


def Calibrate():
    g_window['-CALIBRATE-'].update(disabled=True)
    logger.info("Calibrating robot...")
    time.sleep(5)  # TODO: Call calibrate.
    logger.info("Calibrated robot.")
    g_window['-CALIBRATE-'].update(disabled=False)


def ArgTest(argument):
    print(argument)
    print(type(argument))


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

def HSV(frame):
    lower_boundary = np.array([40, 49, 40])
    upper_boundary = np.array([69, 255, 255])

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_boundary, upper_boundary)
    res = cv2.bitwise_and(frame, frame, mask=mask)

    return res

def main():
    # Setup logging and start app
    logging.basicConfig(level=logging.DEBUG)
    log_queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    # cv2.CAP_DSHOW used because: https://www.reddit.com/r/learnpython/comments/oxo3gd/why_do_i_have_to_use_cv2cap_dshow/
    capture = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

    hsvOnly = False

    while True:
        event, values = g_window.read(timeout=10)

        if event == '-CALIBRATE-':
            calibrateAction = ThreadedAction(Calibrate)
            calibrateAction.start()
            testAction = ThreadedActionArgs(ArgTest, 2)
            testAction.start()

        if event == "-CHECK_BOX_HSV_ONLY-":
            if values["-CHECK_BOX_HSV_ONLY-"] == True:
                hsvOnly = True
            else:
                hsvOnly = False

        elif event == "-EXIT-" or event == sg.WIN_CLOSED or event == None:
            break

        ret, frame = capture.read()
        if hsvOnly:
            frame = HSV(frame)
            


        imgbytes = cv2.imencode(".png", frame)[1].tobytes()
        g_window["-CAMERA_IMAGE-"].update(data=imgbytes)

        # Update Log
        # Poll queue
        try:
            record = log_queue.get(block=False)
        except queue.Empty:
            pass
        else:
            msg = queue_handler.format(record)
            g_window['-LOG-'].update(msg+'\n', append=True)

    g_window.close()


if __name__ == '__main__':
    main()
