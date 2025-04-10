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
            #self.stream = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            self.stream = cv2.VideoCapture(camera_stream_url)
        else:
            # self.stream = cv2.VideoCapture(camera_index)
            self.stream = cv2.VideoCapture(camera_stream_url)

        # If URL is set to "virtual" in Constants.py then use the pre-recorded video instead of the video stream from the Raspberry Pi
        if self.url == "virtual":
            self.stream = cv2.VideoCapture('Camera/VirtualCamVideos/video1.avi')
            self.fps = self.stream.get(cv2.CAP_PROP_FPS)
      
        # This would be important if we directly pull from the camera instead of a stream.
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
        
        # Only needed to capture new video for virtual cam
        #self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        #self.videoWriter = cv2.VideoWriter('output_video.avi', self.fourcc, fps, (frame_width, frame_height))  


    def start(self):
        self.stopped = False
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
                try:
                    (self.grabbed, tmp_frame) = self.stream.read()
                    #self.videoWriter.write(tmp_frame) 
                    tmp_frame = cv2.rotate(
                        tmp_frame, rotateCode=cv2.ROTATE_90_CLOCKWISE)
                    tmp_frame = cv2.flip(tmp_frame, 1)  # Flip horizontally
                    # Flip again to mirror so the bot starts in the top right corner.
                    tmp_frame = cv2.flip(tmp_frame, 1)
                    self.frame = tmp_frame
                    self.new_frame = True
                except Exception as e:
                    print("Error reading frame:", e)
            elapsed_time = time.time() - start_time
            time.sleep(max(0, frame_time - elapsed_time))

    def stop(self):
        self.stopped = True
        #self.videoWriter.release()

    def __del__(self):
        self.stream.release()