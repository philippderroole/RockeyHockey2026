import cv2
import time
from threading import Thread

from Constants import *


class Camera:
    def __init__(self, camera_index, frame_width, frame_height, fps):
        self.stream = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.stream.set(cv2.CAP_PROP_FPS, fps)
        self.stream.set(cv2.CAP_PROP_FOCUS, CAMERA_FOCUS)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFERSIZE)
        (self.grabbed, self.frame) = self.stream.read()

    def get_frame(self):
        return self.stream.read()

    def __del__(self):
        self.stream.release()
