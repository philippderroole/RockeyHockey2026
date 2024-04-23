import cv2
import numpy as np
from Constants import *

def processFrame(frame, sliders):
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

    # TODO: This is eating performance
    # Robot Detection eats more than puck detection.
    # Detect the puck and update UI values.
    ((x, y), radius), ((robotX, robotY), robotRadius) = detectPuck(
        frame, [(lowerBoundary, upperBoundary, puckMinRadius, puckMaxRadius), (robotLowerBoundary, robotUpperBoundary, robotMinRadius, robotMaxRadius)]
    )

    print(f"Puck: {x:.0f},{y:.0f} Radius: {radius:.0f}")
    print(f"Robot: {robotX:.0f},{robotY:.0f} Radius: {robotRadius:.0f}")

    # Mark Puck
    if x != -1 and y != -1 and radius != -1:
        frame = markInFrame(frame, x, y, radius, FRAME_PUCK_OUTLINE_COLOR)
    # Mark robot
    if robotX != -1 and robotY != -1 and robotRadius != -1:
        frame = markInFrame(frame, robotX, robotY,
                            robotRadius, FRAME_ROBOT_OUTLINE_COLOR)
    frame = markRobotRectangle(frame)

    return x, y, radius, robotX, robotY, robotRadius


def detectPuck_old(filteredFrame, lowerBoundary, upperBoundary):
    hsv = cv2.cvtColor(filteredFrame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lowerBoundary, upperBoundary)
    mask_blur = cv2.medianBlur(mask, 19)
    contours, hierarchy = cv2.findContours(mask_blur, 1, 2)
    if not contours:
        return ((0, 0), 0)
    cnt = contours[0]
    (x, y), radius = cv2.minEnclosingCircle(cnt)
    return (x, y), radius


def detectPuck(filteredFrame, boundaries):
    hsv = cv2.cvtColor(filteredFrame, cv2.COLOR_BGR2HSV)

    results = []
    for (lowerBoundary, upperBoundary, minRadius, maxRadius) in boundaries:
        mask = cv2.inRange(hsv, lowerBoundary, upperBoundary)
        mask_blur = cv2.medianBlur(mask, 19)
        contours, hierarchy = cv2.findContours(mask_blur, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
