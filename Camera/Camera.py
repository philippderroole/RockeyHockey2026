import cv2
import time
from threading import Thread

from Constants import *


class Camera:
    def __init__(self, calibration=None):
        self.stream = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_FRAME_WIDTH)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_FRAME_HEIGHT)
        self.stream.set(cv2.CAP_PROP_FPS, CAMERA_FRAMERATE)
        self.stream.set(cv2.CAP_PROP_FOCUS, CAMERA_FOCUS)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFERSIZE)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        self.framesSinceLastRequest = 0
        self.framerate = CAMERA_FRAMERATE
        self.camera_calibration = calibration
        if self.camera_calibration is not None:
            self.camera_calibration.choose()
        self.currentTime = time.time()
        self.previousTime = time.time()

    def start(self):
        print("not implemented yet")

    def stop(self):
        print("not implemented yet")

    def get_frame(self):
        #print("not implemented yet")
        return self.stream.read()
