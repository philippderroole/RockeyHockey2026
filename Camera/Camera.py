import cv2
import time
from threading import Thread


class Camera:
    def __init__(self, camera=0, framerate=60, calibration=None):
        self.stream = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)
        self.stream.set(cv2.CAP_PROP_FPS, 60)
        self.stream.set(cv2.CAP_PROP_FOCUS, 5)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        self.framesSinceLastRequest = 0
        self.framerate = framerate
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
        print("not implemented yet")
