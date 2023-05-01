import cv2
import numpy as np

def filterFrameHSV(frame, lowerBoundary, upperBoundary):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lowerBoundary, upperBoundary)
    filteredFrame = cv2.bitwise_and(frame, frame, mask=mask)
    return filteredFrame