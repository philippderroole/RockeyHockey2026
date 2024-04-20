import cv2
from Constants import *
from datetime import datetime

camera = None
currentFrameTimestamp = datetime.now()
lastFrameTimestamp = datetime.now()

camera = cv2.VideoCapture("http://192.168.178.81:8080/video")
print(camera)
print(camera.getBackendName())
print(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(camera.get(cv2.CAP_PROP_FRAME_WIDTH))

camera.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_FRAME_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_FRAME_HEIGHT)

print("Initial FPS: ", camera.get(cv2.CAP_PROP_FPS))

frame_set = camera.set(cv2.CAP_PROP_FPS, CAMERA_FRAMERATE)

if not frame_set:
    print(f"Failed to set FPS to {CAMERA_FRAMERATE}")
else:
    print(f"FPS set to {CAMERA_FRAMERATE}")

print("Current FPS: ", camera.get(cv2.CAP_PROP_FPS))

camera.set(cv2.CAP_PROP_FOCUS, CAMERA_FOCUS)
camera.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFERSIZE)

print(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(camera.get(cv2.CAP_PROP_FRAME_WIDTH))

while (True):
    currentFrameTimestamp = datetime.now()
    grabbed, frame = camera.read()
    frameTimeMs = (currentFrameTimestamp -
                lastFrameTimestamp).microseconds / 1000
    lastFrameTimestamp = currentFrameTimestamp
    fps = 1000 / frameTimeMs
    print(f"Frame Time: {frameTimeMs:.0f}ms ({fps:.0f} FPS)")