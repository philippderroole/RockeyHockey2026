import cv2
from threading import Thread
import time
import platform
import numpy as np
import requests
from io import BytesIO

class Camera:
    def __init__(
            self, camera_index, frame_width, frame_height, focus, buffer_size, fps, camera_stream_url
    ):
        self.fps = fps
        self.url = camera_stream_url
        # Check if we are running on windows because then we need the CAP_DSHOW flag.
        if platform.system() == "Windows":
            # self.stream = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            self.stream = cv2.VideoCapture(camera_stream_url)
        else:
            self.stream = cv2.VideoCapture(camera_index)
            # self.stream = cv2.VideoCapture(camera_stream_url)
            
        # self.stream.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
        # # self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        # self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        # # self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        # self.stream.set(cv2.CAP_PROP_FPS, fps)
        # print("Initial FPS: ", self.stream.get(cv2.CAP_PROP_FPS))
        # self.stream.set(cv2.CAP_PROP_FOCUS, focus)
        # self.stream.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
        # (self.grabbed, self.frame) = self.stream.read()
        self.grabbed = True
        self.stopped = False
        self.new_frame = False

    def start(self):
        Thread(target=self.get_next_frame, args=()).start()
        # Thread(target=self.fetch_image_from_url, args=()).start()
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
                (self.grabbed, tmp_frame) = self.stream.read()
                tmp_frame = cv2.rotate(
                    tmp_frame, rotateCode=cv2.ROTATE_90_CLOCKWISE)
                tmp_frame = cv2.flip(tmp_frame, 1)  # Flip horizontally
                # Flip again to mirror so the bot starts in the top right corner.
                tmp_frame = cv2.flip(tmp_frame, 1)
                self.frame = tmp_frame
                self.new_frame = True
            elapsed_time = time.time() - start_time
            time.sleep(max(0, frame_time - elapsed_time))

    def fetch_image_from_url(self):
        while not self.stopped:
            start_time = time.time()  # Start the timer
            try:
                response = requests.get(self.url)
                if response.status_code == 200:
                    image_bytes = BytesIO(response.content)
                    image_array = np.asarray(bytearray(image_bytes.read()), dtype=np.uint8)
                    tmp_frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    # tmp_frame = cv2.rotate(
                    #     tmp_frame, rotateCode=cv2.ROTATE_90_CLOCKWISE)
                    # tmp_frame = cv2.flip(tmp_frame, 1)
                    # tmp_frame = cv2.flip(tmp_frame, 1)
                    self.frame = tmp_frame
                    self.new_frame = True
                else:
                    print("Failed to fetch image. Status code:", response.status_code)
                    return None
            except Exception as e:
                print("An error occurred:", e)
                return None
            finally:
                end_time = time.time()  # End the timer
                print("Time taken for this run: {:.2f} seconds".format(end_time - start_time))

    def stop(self):
        self.stopped = True

    def __del__(self):
        self.stream.release()