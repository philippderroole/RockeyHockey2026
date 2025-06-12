import cv2
from threading import Thread
import time
import platform
import numpy as np
import requests
from io import BytesIO
from PyQt5.QtCore import Qt

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
        if(self.url != "virtual"):
            Thread(target=self.read_next_frame_continuously, args=()).start()
        else:
            Thread(target=self.read_next_frame_continuously_at_desired_rate, args=()).start() # Use framerate control so the pre-recorded video for the virtual cam doesnt run as quick as possible
        return self

    def get_current_frame(self):
        self.new_frame = False
        return self.frame

    def get_current_frame_with_timestamp(self):
        self.new_frame = False
        return self.frame, self.frame_timestamp
    
    # Since grab_frame_from_stream blocks until a new frame is available, this reads frames at the camera's exact FPS
    def read_next_frame_continuously(self):
         while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                self.grab_frame_from_stream()
    
    # The framerate is manually controlled here (used for virtual cam)
    def read_next_frame_continuously_at_desired_rate(self):
        fps = self.fps  # desired framerate
        frame_duration = 1.0 / fps
        next_frame_time = time.perf_counter() # Target time for the next frame

        while not self.stopped:
            now = time.perf_counter()
            # Sleep until it's time for the next frame, if we're ahead of schedule
            if now < next_frame_time:
                time.sleep(next_frame_time - now) 
            # Schedule the next frame time in advance (prevents drift)
            next_frame_time += frame_duration  

            #grab next frame
            if not self.grabbed:
                self.stop() 
            else:
                self.grab_frame_from_stream()

            # If we're running behind, resync the clock. This prevents cumulative lag over time
            now = time.perf_counter()
            if now > next_frame_time:
                next_frame_time = now

    #Grabs the next frame from the pi stream and timestamps it. This blocks until a new frame arrives from the Pi stream.
    def grab_frame_from_stream(self):
        try:
            # Read new frame (blocking)
            (self.grabbed, tmp_frame) = self.stream.read()  
            # Create timestamp for the frame (could be done by physical camera for better precision)
            self.temp_timestamp = time.perf_counter() 
            # Rotate the frame (should propably be done somewhere else)
            tmp_frame = cv2.rotate(tmp_frame, rotateCode=cv2.ROTATE_90_CLOCKWISE) 
            self.frame = tmp_frame 
            self.frame_timestamp = self.temp_timestamp
            self.new_frame = True 
        except Exception as e:
            print("Error reading frame:", e)

    def stop(self):
        self.stopped = True
        #self.videoWriter.release()

    def __del__(self):
        self.stream.release()

        
# with this algorithm the user does not have to set 
# the corner points in a specific order
def order_points(pts):
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4,2), dtype="float32")

    s = pts.sum(axis= 1)
    rect[0] = pts[np.argmin(s)] #Top-left
    rect[2] = pts[np.argmax(s)] #Bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] #Top-right
    rect[3] = pts[np.argmax(diff)] #Bottom-left

    return rect
#The user can remove a corner with 'r'
#Are the Corners Applied and th user presses 'r' las orner gets removed 
#and the user has to apply all the corners agai
def keyPressEvent(self, event):
        if event.key() == Qt.Key_R and not self.cornersApplied:
            if self.croppedTableCoords:
                removed = self.croppedTableCoords.pop()
                print(f"Removed last corner: {removed}")
