# from StepperController import StepperController
# from Camera import Camera
# from UserInterface import UserInterface
# #controller = StepperController("COM4", 115200)
# camera = Camera(1, 60)
# userInterface = UserInterface(None, camera)

import sys
import cv2
import math
import numpy as np
import qdarkstyle
import time
from datetime import datetime
from collections import deque
from shapely.geometry import LineString, Point
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QSplashScreen,
    QMainWindow,
    QLabel,
    QPushButton,
    QCheckBox,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QSlider,
)

from Constants import *
from Camera import Camera
from StepperController import StepperController
from Processing.ProcessFrame import filterFrameHSV, detectPuck, markPuckInFrame
from Processing.Line import Line


class MoveWorker(QThread):
    def __init__(self, stepperController, parent=None):
        super().__init__(parent)
        self.mutex = QMutex()
        self.stepperController = stepperController
        self.x = None
        self.y = None

    def run(self):
        while True:
            # Wait for x and y to be set by the main thread
            # with QMutexLocker(self.mutex):
            while self.x is None or self.y is None:
                # self.mutex.unlock()
                self.msleep(1)
                # self.mutex.lock()
            x, y = self.x, self.y
            self.x = None
            self.y = None
            # print(f"Moving X={x}, Y={y}")
            if self.stepperController != None:
                self.stepperController.move_to_position(int(x), int(y))

    def set_values(self, x, y):
        # with QMutexLocker(self.mutex):
        self.x = x
        self.y = y


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rocky Hockey 2023")

        # Create a label to display the camera image.
        self.cameraImageLabel = QLabel(self)
        self.cameraImageLabel.setAlignment(Qt.AlignCenter)
        self.cameraImageLabel.mousePressEvent = self.getImageClickPos

        self.filteredImageLabel = QLabel(self)
        self.filteredImageLabel.setAlignment(Qt.AlignCenter)

        # Create a log textbox.
        self.logTextbox = QTextEdit(self)
        self.logTextbox.setReadOnly(True)

        # Create the "Exit" button.
        self.exitButton = QPushButton("Exit", self)
        self.exitButton.clicked.connect(self.exitApp)

        # Create the "Calibrate" button.
        self.calibrateButton = QPushButton("Calibrate", self)
        self.calibrateButton.clicked.connect(self.calibrate)

        # Create the "Move To Position" button.
        self.moveToPositionButton = QPushButton("Move To Position", self)
        self.moveToPositionButton.clicked.connect(self.moveToPosition)

        # Create the "Maxima" button.
        self.getMaximaButton = QPushButton("Get Maxima", self)
        self.getMaximaButton.clicked.connect(self.getMaxima)

        self.xCoordTextBox = QTextEdit()
        self.xCoordTextBox.setFixedHeight(25)
        self.xCoordTextBox.setText("0")
        self.yCoordTextBox = QTextEdit()
        self.yCoordTextBox.setFixedHeight(25)
        self.yCoordTextBox.setText("0")

        self.controlHorizontalBox = QHBoxLayout()
        self.controlHorizontalBox.addWidget(self.calibrateButton)
        self.controlHorizontalBox.addWidget(self.getMaximaButton)
        self.controlHorizontalBox.addWidget(self.moveToPositionButton)
        self.controlHorizontalBox.addWidget(QLabel(text="X"))
        self.controlHorizontalBox.addWidget(self.xCoordTextBox)
        self.controlHorizontalBox.addWidget(QLabel(text="Y"))
        self.controlHorizontalBox.addWidget(self.yCoordTextBox)

        # Create the sliders for adjusting the filters.
        # We need the upper and lower bounds for Hue, Saturation and Value.
        self.lowerHueSlider = QSlider(Qt.Horizontal)
        self.lowerSaturationSlider = QSlider(Qt.Horizontal)
        self.lowerValueSlider = QSlider(Qt.Horizontal)
        self.upperHueSlider = QSlider(Qt.Horizontal)
        self.upperSaturationSlider = QSlider(Qt.Horizontal)
        self.upperValueSlider = QSlider(Qt.Horizontal)

        self.lowerHueSlider.setMinimum(0)
        self.lowerHueSlider.setMaximum(255)
        self.lowerSaturationSlider.setMinimum(0)
        self.lowerSaturationSlider.setMaximum(255)
        self.lowerValueSlider.setMinimum(0)
        self.lowerValueSlider.setMaximum(255)
        self.upperHueSlider.setMinimum(0)
        self.upperHueSlider.setMaximum(255)
        self.upperSaturationSlider.setMinimum(0)
        self.upperSaturationSlider.setMaximum(255)
        self.upperValueSlider.setMinimum(0)
        self.upperValueSlider.setMaximum(255)

        self.lowerHueSlider.setValue(CAMERA_LOWER_HUE)
        self.lowerSaturationSlider.setValue(CAMERA_LOWER_SATURATION)
        self.lowerValueSlider.setValue(CAMERA_LOWER_VALUE)
        self.upperHueSlider.setValue(CAMERA_UPPER_HUE)
        self.upperSaturationSlider.setValue(CAMERA_UPPER_SATURATION)
        self.upperValueSlider.setValue(CAMERA_UPPER_VALUE)

        self.lowerHueLabel = QLabel(str(self.lowerHueSlider.value()))
        self.lowerSaturationLabel = QLabel(str(self.lowerSaturationSlider.value()))
        self.lowerValueLabel = QLabel(str(self.lowerValueSlider.value()))
        self.upperHueLabel = QLabel(str(self.upperHueSlider.value()))
        self.upperSaturationLabel = QLabel(str(self.upperSaturationSlider.value()))
        self.upperValueLabel = QLabel(str(self.upperValueSlider.value()))

        self.lowerHueSlider.valueChanged.connect(
            lambda value: self.lowerHueLabel.setText(str(value))
        )
        self.lowerSaturationSlider.valueChanged.connect(
            lambda value: self.lowerSaturationLabel.setText(str(value))
        )
        self.lowerValueSlider.valueChanged.connect(
            lambda value: self.lowerValueLabel.setText(str(value))
        )
        self.upperHueSlider.valueChanged.connect(
            lambda value: self.upperHueLabel.setText(str(value))
        )
        self.upperSaturationSlider.valueChanged.connect(
            lambda value: self.upperSaturationLabel.setText(str(value))
        )
        self.upperValueSlider.valueChanged.connect(
            lambda value: self.upperValueLabel.setText(str(value))
        )

        self.lowerHueHbox = QHBoxLayout()
        self.lowerSaturationHbox = QHBoxLayout()
        self.lowerValueHbox = QHBoxLayout()
        self.upperHueHbox = QHBoxLayout()
        self.upperSaturationHbox = QHBoxLayout()
        self.upperValueHbox = QHBoxLayout()

        self.lowerHueLabelText = QLabel(text="Lower Hue: ")
        self.lowerSaturationLabelText = QLabel(text="Lower Saturation: ")
        self.lowerValueLabelText = QLabel(text="Lower Value: ")
        self.upperHueLabelText = QLabel(text="Upper Hue: ")
        self.upperSaturationLabelText = QLabel(text="Upper Saturation: ")
        self.upperValueLabelText = QLabel(text="Upper Value: ")

        self.lowerHueLabelText.setFixedWidth(150)
        self.lowerSaturationLabelText.setFixedWidth(150)
        self.lowerValueLabelText.setFixedWidth(150)
        self.upperHueLabelText.setFixedWidth(150)
        self.upperSaturationLabelText.setFixedWidth(150)
        self.upperValueLabelText.setFixedWidth(150)

        self.lowerHueHbox.addWidget(self.lowerHueLabelText)
        self.lowerHueHbox.addWidget(self.lowerHueLabel)
        self.lowerHueHbox.addWidget(self.lowerHueSlider)

        self.lowerSaturationHbox.addWidget(self.lowerSaturationLabelText)
        self.lowerSaturationHbox.addWidget(self.lowerSaturationLabel)
        self.lowerSaturationHbox.addWidget(self.lowerSaturationSlider)

        self.lowerValueHbox.addWidget(self.lowerValueLabelText)
        self.lowerValueHbox.addWidget(self.lowerValueLabel)
        self.lowerValueHbox.addWidget(self.lowerValueSlider)

        self.upperHueHbox.addWidget(self.upperHueLabelText)
        self.upperHueHbox.addWidget(self.upperHueLabel)
        self.upperHueHbox.addWidget(self.upperHueSlider)

        self.upperSaturationHbox.addWidget(self.upperSaturationLabelText)
        self.upperSaturationHbox.addWidget(self.upperSaturationLabel)
        self.upperSaturationHbox.addWidget(self.upperSaturationSlider)

        self.upperValueHbox.addWidget(self.upperValueLabelText)
        self.upperValueHbox.addWidget(self.upperValueLabel)
        self.upperValueHbox.addWidget(self.upperValueSlider)

        self.filterVbox = QVBoxLayout()
        self.filterVbox.addLayout(self.lowerHueHbox)
        self.filterVbox.addLayout(self.lowerSaturationHbox)
        self.filterVbox.addLayout(self.lowerValueHbox)
        self.filterVbox.addLayout(self.upperHueHbox)
        self.filterVbox.addLayout(self.upperSaturationHbox)
        self.filterVbox.addLayout(self.upperValueHbox)

        # Create the right vertical box.
        self.vboxRight = QVBoxLayout()
        self.hboxImages = QHBoxLayout()

        # self.vboxRight.addWidget(QLabel(text="Filtered Image"))
        self.hboxImages.addWidget(self.filteredImageLabel)
        # self.vboxRight.addWidget(QLabel(text="Camera Image"))
        self.hboxImages.addWidget(self.cameraImageLabel)
        self.vboxRight.addLayout(self.hboxImages)

        # Puck values.
        self.puckValuesHbox = QHBoxLayout()
        self.puckXLabel = QLabel(text="X: 0")
        self.puckYLabel = QLabel(text="Y: 0")
        self.puckRadiusLabel = QLabel(text="Radius: 0")
        self.puckVecLabel = QLabel(text="Vec: 0")
        self.puckSpeedLabel = QLabel(text="Speed: 0")
        self.puckValuesHbox.addWidget(QLabel(text="Puck Values: "))
        self.puckValuesHbox.addWidget(self.puckXLabel)
        self.puckValuesHbox.addWidget(self.puckYLabel)
        self.puckValuesHbox.addWidget(self.puckRadiusLabel)
        self.puckValuesHbox.addWidget(self.puckVecLabel)
        self.puckValuesHbox.addWidget(self.puckSpeedLabel)

        # Corner setting.
        self.cornersHBox = QHBoxLayout()
        self.cornersApplyButton = QPushButton("Apply Corners", self)
        self.cornersApplyButton.clicked.connect(self.applyCorners)
        self.cornersResetButton = QPushButton("Reset Corners", self)
        self.cornersResetButton.clicked.connect(self.resetCorners)
        self.cornersHBox.addWidget(self.cornersApplyButton)
        self.cornersHBox.addWidget(self.cornersResetButton)

        self.botSettingsHBox = QHBoxLayout()
        self.botSettingsHBox.addWidget(QLabel(text="Bot Settings: "))
        self.botSettingsHBox.addWidget(QLabel(text="SpeedThreshold: "))
        self.speedThresholdSlider = QSlider(Qt.Horizontal)
        self.botSettingsHBox.addWidget(self.speedThresholdSlider)
        self.speedThresholdSlider.setMinimum(0)
        self.speedThresholdSlider.setMaximum(200)

        self.speedThresholdSlider.setValue(SPEED_THRESHOLD)
        self.speedThresholdLabel = QLabel(str(self.speedThresholdSlider.value()))
        self.botSettingsHBox.addWidget(self.speedThresholdLabel)
        self.speedThresholdSlider.valueChanged.connect(
            lambda value: self.speedThresholdLabel.setText(str(value))
        )

        self.activateBotCheckBox = QCheckBox("Activate Bot")
        self.botSettingsHBox.addWidget(self.activateBotCheckBox)
        self.activateBotCheckBox.clicked.connect(self.setBotState)
        self.activateBotCheckBox.setCheckState(Qt.CheckState.Unchecked)

        # Create the left vertical box.
        self.vboxLeft = QVBoxLayout()
        self.vboxLeft.addLayout(self.controlHorizontalBox)
        self.vboxLeft.addWidget(QLabel(text="Adjust filters"))
        self.vboxLeft.addLayout(self.filterVbox)
        self.vboxLeft.addLayout(self.puckValuesHbox)
        self.vboxLeft.addLayout(self.cornersHBox)
        self.vboxLeft.addLayout(self.botSettingsHBox)
        self.vboxLeft.addWidget(self.logTextbox)
        # self.vboxLeft.addWidget(self.calibrateButton)
        # self.vboxLeft.addWidget(self.gotoPositionButton)
        self.vboxLeft.addWidget(self.exitButton)

        self.hboxMain = QHBoxLayout()

        # Create a central widget to hold the layouts
        self.CentralWidget = QWidget()
        self.CentralWidget.setLayout(self.hboxMain)

        # Set the central widget and add the horizontal layout to the bottom
        self.setCentralWidget(self.CentralWidget)
        self.hboxMain.addLayout(self.vboxLeft)
        self.hboxMain.addLayout(self.vboxRight)

        # Create a timer to continuously update the camera image
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateImages)
        self.timer.start(1)

        # Camera used for image.
        self.camera = Camera(
            CAMERA_INDEX,
            CAMERA_FRAME_WIDTH,
            CAMERA_FRAME_HEIGHT,
            CAMERA_FOCUS,
            CAMERA_BUFFERSIZE,
            CAMERA_FRAMERATE,
        ).start()
        self.stepperController = None
        # Stepper Controller
        try:
            self.stepperController = StepperController(
                STEPPER_COM_PORT, STEPPER_BAUDRATE
            )
            self.stepperController.connect()
        except Exception:
            self.logTextbox.append(
                "ERROR: No Arduino found on " + STEPPER_COM_PORT + "."
            )
            self.stepperController = None

        self.moveWorker = MoveWorker(stepperController=self.stepperController)
        self.moveWorker.start()

        self.tableCordnerCoords = [(TABLE_CORNER_TOP_LEFT_X, TABLE_CORNER_TOP_LEFT_Y),
                                   (TABLE_CORNER_TOP_RIGHT_X, TABLE_CORNER_TOP_RIGHT_Y),
                                   (TABLE_CORNER_BOTTOM_RIGHT_X, TABLE_CORNER_BOTTOM_RIGHT_Y),
                                   (TABLE_CORNER_BOTTOM_LEFT_X, TABLE_CORNER_BOTTOM_LEFT_Y)]

        self.cornersApplied = True
        self.originalCorners = np.float32(
            [
                [0, 0],
                [CAMERA_FRAME_HEIGHT - 1, 0],
                [CAMERA_FRAME_HEIGHT - 1, CAMERA_FRAME_WIDTH - 1],
                [0, CAMERA_FRAME_WIDTH - 1],
            ]
        )

        self.speedThreshold = SPEED_THRESHOLD

        self.upperBorder = [(0, 0), (CAMERA_FRAME_WIDTH, 0)]
        self.lowerBorder = [
            (0, CAMERA_FRAME_HEIGHT),
            (CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT),
        ]
        self.leftBorder = [(0, 0), (0, CAMERA_FRAME_HEIGHT)]
        self.rightBorder = [
            (CAMERA_FRAME_WIDTH, 0),
            (CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT),
        ]

        self.lastPosition = (0, 0)
        self.currentPosition = (0, 0)
        self.frameCounter = 0
        self.moveForward = True

        self.puckPositions = deque(maxlen=MAX_PUCK_POSITION_BUFFER)
        self.positionsSent = 0

        self.botActivated = False

    def closeEvent(self, event):
        # Let the window close.
        event.accept()
        self.exitApp()

    def exitApp(self):
        self.timer.stop()
        self.camera.stop()
        sys.exit()

    def mainLoop(self):
        while True:
            self.updateImages()

    def setBotState(self):
        if self.activateBotCheckBox.checkState() == Qt.CheckState.Checked:
            self.botActivated = True
        else:
            self.botActivated = False

    def applyCorners(self):
        if len(self.tableCordnerCoords) == 4:
            self.logTextbox.append(
                "Applied corners. Fitting image. If the image does not look right then reset the corners. Start at the top left and then go counter clock wise."
            )
            self.cornersApplied = True
        else:
            self.logTextbox.append(
                "ERROR: Not all corners set. There must be 4 corners set. Use left click to set the corners."
            )
            self.cornersApplied = False

    def resetCorners(self):
        self.logTextbox.append("Reset corners. Resetting image fit.")
        self.cornersApplied = False
        self.tableCordnerCoords = []

    def getImageClickPos(self, event):
        # The Camera image is double the size of the debug window image.
        x = event.pos().x() * 2
        y = event.pos().y() * 2
        print(f"Clicked x:{x}, y:{y}")
        # 1 is left click, 2 is right click
        mouseButton = event.button()
        if mouseButton == 1 and len(self.tableCordnerCoords) < 4:
            self.tableCordnerCoords.append((x, y))

    def sendMoveValues(self, x, y):
        self.moveWorker.set_values(x, y)

    def calibrate(self):
        # Add your calibration code here
        if self.stepperController is not None:
            self.logTextbox.append("Calibrating...")
            self.stepperController.calibrate()
            self.isAtZero = True
        else:
            self.logTextbox.append(
                "ERROR: Cannot calibrate. No Arduino found on " + STEPPER_COM_PORT + "."
            )

    def getMaxima(self):
        if self.stepperController is not None:
            x, y = self.stepperController.get_maxima()
            self.logTextbox.append(f"Maxima: X={x}, Y={y}")
        else:
            self.logTextbox.append(
                "ERROR: Cannot get maxima. No Arduino found on "
                + STEPPER_COM_PORT
                + "."
            )

    def moveToPosition(self):
        if self.stepperController is not None:
            try:
                x = int(self.xCoordTextBox.toPlainText())
                y = int(self.yCoordTextBox.toPlainText())
                self.logTextbox.append("Moving to X=" + str(x) + ",Y=" + str(y))
                self.sendMoveValues(x, y)
            except ValueError:
                self.logTextbox.append(
                    "ERROR: X and/or Y value is not an integer. Cannot move to position."
                )
        else:
            self.logTextbox.append(
                "ERROR: Cannot move to position. No Arduino found on "
                + STEPPER_COM_PORT
                + "."
            )

    def updateImages(self):
        if self.camera.new_frame:
            frame = self.camera.get_current_frame()
            # Rotate the camera frame so we have it in "portrait mode" and the robot is on top.
            frame = cv2.rotate(frame, rotateCode=cv2.ROTATE_90_CLOCKWISE)

            if self.cornersApplied:
                # If the corners are set then fit the image.
                # Corners have to be inputted counter clockwise.
                selectedCorners = np.float32(
                    [
                        [self.tableCordnerCoords[0][0], self.tableCordnerCoords[0][1]],
                        [self.tableCordnerCoords[1][0], self.tableCordnerCoords[1][1]],
                        [self.tableCordnerCoords[2][0], self.tableCordnerCoords[2][1]],
                        [self.tableCordnerCoords[3][0], self.tableCordnerCoords[3][1]],
                    ]
                )

                # Calculate transformation matrix.
                matrix = cv2.getPerspectiveTransform(
                    selectedCorners, self.originalCorners
                )
                # Warp the image.
                frame = cv2.warpPerspective(
                    frame, matrix, (CAMERA_FRAME_HEIGHT, CAMERA_FRAME_WIDTH)
                )
                frame = cv2.resize(frame, (CAMERA_FRAME_HEIGHT, CAMERA_FRAME_WIDTH))

            if self.cornersApplied == False:
                # Draw the corners if they are set.
                for corner in self.tableCordnerCoords:
                    cv2.circle(frame, (corner[0], corner[1]), 5, (255, 255, 255), 2)

            self.frameCounter = self.frameCounter + 1
            lowerBoundary = np.array(
                [
                    self.lowerHueSlider.value(),
                    self.lowerSaturationSlider.value(),
                    self.lowerValueSlider.value(),
                ]
            )
            upperBoundary = np.array(
                [
                    self.upperHueSlider.value(),
                    self.upperSaturationSlider.value(),
                    self.upperValueSlider.value(),
                ]
            )
            filteredFrame = filterFrameHSV(frame, lowerBoundary, upperBoundary)

            # Detect the puck and update UI values.
            (x, y), radius = detectPuck(filteredFrame, lowerBoundary, upperBoundary)
            frame = markPuckInFrame(frame, x, y, radius)
            self.currentPosition = (x, y)

            self.puckPositions.append((x, y))

            self.puckXLabel.setText(str(f"X: {x:.1f}"))
            self.puckYLabel.setText(str(f"Y: {y:.1f}"))
            self.puckRadiusLabel.setText(str(f"Radius: {radius:.1f}"))

            avgPositionX = sum(pos[0] for pos in self.puckPositions) / len(
                self.puckPositions
            )
            avgPositionY = sum(pos[1] for pos in self.puckPositions) / len(
                self.puckPositions
            )

            velocity = (x - avgPositionX, y - avgPositionY)
            self.puckVecLabel.setText(f"Vec: {velocity[0]:.1f}, {velocity[1]:.1f}")

            speed = math.sqrt((velocity[0] * velocity[0] + velocity[1] * velocity[1]))
            self.puckSpeedLabel.setText(f"Speed: {speed:.1f}")

            puckPos = (int(self.currentPosition[0]), int(self.currentPosition[1]))

            goingBack = puckPos[1] > avgPositionY

            if speed > self.speedThresholdSlider.value() and not goingBack:
                line = Line((avgPositionX, avgPositionY), self.currentPosition)
                try:
                    if line.get_m() is not None:
                        # if line.get_angle() >= 0: # left edge
                        #     collisionPoint = (int(0), int(line.get_y(0)))
                        # else: # right edge
                        #     collisionPoint = (int(CAMERA_FRAME_HEIGHT), int(line.get_y(CAMERA_FRAME_HEIGHT)))

                        # reflectionLine = Line(collisionPoint, None, (1 / line.get_m()))
                        # reflectionPoint = (int(CAMERA_FRAME_HEIGHT - reflectionLine.get_x(0)), int(0))
                        # cv2.circle(frame, reflectionPoint, 5, (100, 0, 255), -1)
                        # cv2.line(frame, puckPos, collisionPoint, (255, 255, 255), thickness=1, lineType=4)
                        # cv2.line(frame, collisionPoint, reflectionPoint, (255, 255, 255), thickness=1, lineType=4)
                        # cv2.circle(frame, collisionPoint, 5, (0, 100, 255), -1)

                        finalPoint = (int(line.get_x(50)), 50)
                        cv2.circle(frame, finalPoint, 5, (100, 0, 255), -1)
                        cv2.line(
                            frame,
                            puckPos,
                            finalPoint,
                            (255, 255, 255),
                            thickness=1,
                            lineType=4,
                        )

                        # Puck movement.
                        if self.frameCounter > 2 and x != 0 and y != 0:
                            # self.logTextbox.append(f"Final Point: X={finalPoint[0]}, Y={finalPoint[1]}")

                            if (
                                finalPoint[0] > 20
                                and finalPoint[0] < CAMERA_FRAME_HEIGHT - 20
                            ):
                                moveX, moveY = self.mapCoordinates(
                                    finalPoint[0],
                                    finalPoint[1],
                                    CAMERA_FRAME_HEIGHT,
                                    CAMERA_FRAME_WIDTH,
                                    TABLE_MAX_X,
                                    TABLE_MAX_Y,
                                )
                                # self.logTextbox.append(f"Move To: X={moveX}, Y={moveY}")
                                moveY = 0
                                # X is inverted
                                moveX = TABLE_MAX_X - moveX
                                if self.botActivated:
                                    self.positionsSent += 1
                                    print(f"Sending {self.positionsSent}")
                                    self.sendMoveValues(int(moveX), int(moveY))

                            self.frameCounter = 0
                except:
                    pass
            if len(self.puckPositions) > MAX_PUCK_POSITION_BUFFER:
                self.puckPositions.popleft()

            self.updateImageFromFrame(self.cameraImageLabel, frame)
            self.updateImageFromFrame(self.filteredImageLabel, filteredFrame)

    def mapCoordinates(
        self, x, y, maxWidthFrom, maxHeightFrom, maxWidthTo, maxHeightTo
    ):
        xScale = maxWidthTo / maxWidthFrom
        yScale = maxHeightTo / maxHeightFrom
        x = x * xScale
        y = y * yScale
        return x, y

    def reflection_angle(self, incident_angle, surface_angle):
        # Convert angles to radians
        incident_angle = math.radians(incident_angle)
        surface_angle = math.radians(surface_angle)

        # Calculate the reflection angle
        reflection_angle = 2 * surface_angle - incident_angle

        # Convert reflection angle back to degrees
        reflection_angle = math.degrees(reflection_angle)

        return reflection_angle

    # a is starting point
    # b is middle point (intersection point)
    # c is ending point of line
    def getAngle(self, a, b, c):
        ang = math.degrees(
            math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
        )
        return ang + 360 if ang < 0 else ang

    def line_intersection(self, line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            return False, 0, 0

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return True, x, y
    
    # Returns collisionPoint, intersectsX, intersectsY
    def getPositions(self, prevPuckPos, currPuckPos, defenseY):
        line = Line(prevPuckPos, currPuckPos)
        if line.get_m() is not None:
            if line.get_angle() >= 0:  # left edge
                collision_point = (int(0), int(line.get_y(0)))
            else:  # right edge
                collision_point = (int(CAMERA_FRAME_HEIGHT), int(line.get_y(CAMERA_FRAME_WIDTH)))

            # Collides behind the robot -> so no collision at the wall.
            collidesWithWall = False if collision_point[1] < 0 else True

            yref = collision_point[1] - (currPuckPos[1] - collision_point[1])
            xref = currPuckPos[0]
            reflection_point = (xref, yref)

            if collidesWithWall:
                intersects, intersectsX, intersectsY = self.line_intersection((collision_point, reflection_point), ((0,defenseY), (CAMERA_FRAME_HEIGHT, defenseY)))
            else:
                intersects, intersectsX, intersectsY = self.line_intersection((currPuckPos, collision_point), ((0,defenseY), (CAMERA_FRAME_HEIGHT, defenseY)))
            #cv2.circle(frame, (int(intersectsX), int(intersectsY)), 10, (255, 255, 255), -1) #pink
            return collision_point, intersectsX, intersectsY
        else:
            return None, None, None

    def updateImageFromFrame(self, image, frame):
        # Resize to GUI size.
        frame = cv2.resize(frame, (DEBUG_WINDOW_FRAME_HEIGHT, DEBUG_WINDOW_FRAME_WIDTH))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, ch = frame.shape
        bytesPerLine = ch * width
        qtImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap(qtImg)
        image.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    splash = QSplashScreen(QPixmap("splash.png"))
    splash.show()
    main_window = MainWindow()
    splash.close()
    main_window.show()
    sys.exit(app.exec_())
