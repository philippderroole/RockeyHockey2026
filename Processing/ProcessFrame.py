import cv2
import numpy as np
from Constants import *

lastRobotData = ((0, 0), 0)
lastRobotDetection = 0

def processFrame(frame, sliders):
    global lastRobotData
    global lastRobotDetection

    lowerBoundary = np.array(
        [
            sliders.lowerHueSlider.value(),
            sliders.lowerSaturationSlider.value(),
            sliders.lowerValueSlider.value(),
        ]
    )
    upperBoundary = np.array(
        [
            sliders.upperHueSlider.value(),
            sliders.upperSaturationSlider.value(),
            sliders.upperValueSlider.value(),
        ]
    )
    puckMinRadius = sliders.lowerPuckRadiusSlider.value()
    puckMaxRadius = sliders.upperPuckRadiusSlider.value()

    robotLowerBoundary = np.array([
        sliders.lowerHueRobotSlider.value(),
        sliders.lowerSaturationRobotSlider.value(),
        sliders.lowerValueRobotSlider.value(),
    ])
    robotUpperBoundary = np.array([
        sliders.upperHueRobotSlider.value(),
        sliders.upperSaturationRobotSlider.value(),
        sliders.upperValueRobotSlider.value(),
    ])
    robotMinRadius = sliders.lowerRobotRadiusSlider.value()
    robotMaxRadius = sliders.upperRobotRadiusSlider.value()


    resizeFrame = False
    if CAMERA_FRAME_HEIGHT > 700 or CAMERA_FRAME_WIDTH > 1200:
        resizeFrame = True

    detectRobot = False

    ((x, y), radius), ((robotX, robotY), robotRadius) = detectPuckCustomizeable(
        filteredFrame=frame, 
        boundaries=[(lowerBoundary, upperBoundary, puckMinRadius, puckMaxRadius), (robotLowerBoundary, robotUpperBoundary, robotMinRadius, robotMaxRadius)], 
        resizeFrame=resizeFrame,
        useBlur=False,
        useUMat=False,
        detectRobot=detectRobot
    )

    # If the robot is detected, save the data.
    if detectRobot and robotX != -1 and robotY != -1 and robotRadius != -1:
        lastRobotData = ((robotX, robotY), robotRadius)
    # If the robot is not detected, use the last known data.
    else:
        robotX, robotY = lastRobotData[0]
        robotRadius = lastRobotData[1]

        lastRobotDetection = lastRobotDetection + 1
        if lastRobotDetection >= CAMERA_ROBOT_DETECTION_FREQUENCY:
            lastRobotDetection = 0

    # print(f"Puck: {x:.0f},{y:.0f} Radius: {radius:.0f}")
    # print(f"Robot: {robotX:.0f},{robotY:.0f} Radius: {robotRadius:.0f}")

    # Mark Puck
    if x != -1 and y != -1 and radius != -1:
        frame = markInFrame(frame, x, y, radius, FRAME_PUCK_OUTLINE_COLOR)
    # Mark robot
    if detectRobot and robotX != -1 and robotY != -1 and robotRadius != -1:
        frame = markInFrame(frame, robotX, robotY,
                            robotRadius, FRAME_ROBOT_OUTLINE_COLOR)
    frame = markRobotRectangle(frame)

    return x, y, radius, robotX, robotY, robotRadius

def detectPuckCustomizeable(filteredFrame, boundaries, resizeFrame=False, useBlur=True, useUMat=False, detectRobot=True):
    if resizeFrame:
        filteredFrame = cv2.resize(filteredFrame, (filteredFrame.shape[1] // 2, filteredFrame.shape[0] // 2))

    usedFrame = None
    if useUMat:
        usedFrame = cv2.UMat(filteredFrame)
    else:
        usedFrame = filteredFrame

    hsv = cv2.cvtColor(usedFrame, cv2.COLOR_BGR2HSV)

    results = []
    for i, (lowerBoundary, upperBoundary, minRadius, maxRadius) in enumerate(boundaries):
        mask = cv2.inRange(hsv, lowerBoundary, upperBoundary)

        # i == 1 -> Robot Detection
        if i == 1:
            if not detectRobot:
                # print("Skipping Robot Detection")
                results.append(((-1, -1), -1))
                continue
            # Only consider the upper half of the frame
            # This is not possible when uMat is used
            if not useUMat:
                mask[mask.shape[0]//2:, :] = 0

        usedMask = None
        if useBlur:
            # Blur Mask
            usedMask = cv2.medianBlur(mask, 5)
        else:
            usedMask = mask
        contours, hierarchy = cv2.findContours(usedMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            if minRadius <= radius <= maxRadius:
                results.append(((x, y), radius))
                break
        else:
            results.append(((-1, -1), -1))

    return results

def markInFrame(frame, x, y, radius, color):
    # Convert to int.
    center = (int(x), int(y))
    radius = int(radius)
    # Draw a circle around the puck in the unfiltered image.
    cv2.circle(frame, center, radius, color, 2)
    return frame


def markRobotRectangle(frame):
    # Only needs top left and bottom right corner.
    cv2.rectangle(frame, (0, 0, CAMERA_FRAME_HEIGHT, CAMERA_FRAME_ROBOT_MAX_Y), (0, 0, 255), 1)
    return frame
