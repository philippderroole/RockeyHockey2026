import os

import cv2
from threading import Thread
import time


class Camera:
    def __init__(
            self, camera_index, frame_width, frame_height, focus, buffer_size, fps
    ):
        self.fps = fps
        self.stream = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
        self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('X', 'V', 'I', 'D'))
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.stream.set(cv2.CAP_PROP_FPS, fps)
        self.stream.set(cv2.CAP_PROP_FOCUS, focus)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)

        (self.grabbed, self.frame) = self.stream.read()

        self.stopped = False
        self.new_frame = False

    def start(self):
        Thread(target=self.get_next_frame, args=()).start()
        return self

    def get_current_frame(self):
        self.new_frame = False
        return self.frame

    def get_next_frame(self):
        fps = self.fps  # Desired frame rate
        frame_time = 1 / fps
        while not self.stopped:
            start_time = time.time()
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()
                self.frame = cv2.rotate(self.frame, rotateCode=cv2.ROTATE_90_CLOCKWISE)
                self.new_frame = True
            elapsed_time = time.time() - start_time
            time.sleep(max(0, frame_time - elapsed_time))

    def stop(self):
        self.stopped = True

    def __del__(self):
        self.stream.release()
