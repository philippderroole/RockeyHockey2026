import cv2
from threading import Thread


class Camera:
    def __init__(
        self, camera_index, frame_width, frame_height, focus, buffer_size, fps
    ):
        self.stream = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
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
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()
                self.new_frame = True

    def stop(self):
        self.stopped = True

    def __del__(self):
        self.stream.release()
