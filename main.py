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
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMainWindow, QLabel, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QSlider

from Constants import *
from Camera import Camera
from StepperController import StepperController
from Processing.ProcessFrame import filterFrameHSV, detectPuck, markPuckInFrame

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
            with QMutexLocker(self.mutex):
                while self.x is None or self.y is None:
                    self.mutex.unlock()
                    self.msleep(10)
                    self.mutex.lock()
                x, y = self.x, self.y
                self.x = None
                self.y = None
            #print(f"Moving X={x}, Y={y}")
            self.stepperController.move_to_position(int(x), int(y))

    def set_values(self, x, y):
        with QMutexLocker(self.mutex):
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

        self.lowerHueSlider.valueChanged.connect(lambda value: self.lowerHueLabel.setText(str(value)))
        self.lowerSaturationSlider.valueChanged.connect(lambda value: self.lowerSaturationLabel.setText(str(value)))
        self.lowerValueSlider.valueChanged.connect(lambda value: self.lowerValueLabel.setText(str(value)))
        self.upperHueSlider.valueChanged.connect(lambda value: self.upperHueLabel.setText(str(value)))
        self.upperSaturationSlider.valueChanged.connect(lambda value: self.upperSaturationLabel.setText(str(value)))
        self.upperValueSlider.valueChanged.connect(lambda value: self.upperValueLabel.setText(str(value)))

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
        #self.vboxRight.addWidget(QLabel(text="Filtered Image"))
        self.vboxRight.addWidget(self.filteredImageLabel)
        #self.vboxRight.addWidget(QLabel(text="Camera Image"))
        self.vboxRight.addWidget(self.cameraImageLabel)

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

        # Create the left vertical box.
        self.vboxLeft = QVBoxLayout()
        self.vboxLeft.addLayout(self.controlHorizontalBox)        
        self.vboxLeft.addWidget(QLabel(text="Adjust filters"))
        self.vboxLeft.addLayout(self.filterVbox)
        self.vboxLeft.addLayout(self.puckValuesHbox)
        self.vboxLeft.addLayout(self.cornersHBox)
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
        self.timer.start(30)

        # Camera used for image.
        self.camera = Camera(CAMERA_INDEX, CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT, CAMERA_FOCUS, CAMERA_BUFFERSIZE, CAMERA_FRAMERATE)
        self.stepperController = None
        # Stepper Controller
        try:
            self.stepperController = StepperController(STEPPER_COM_PORT, STEPPER_BAUDRATE)        
        except Exception:
            self.logTextbox.append("ERROR: No Arduino found on " + STEPPER_COM_PORT + ".")

        self.stepperController.connect()

        self.moveWorker = MoveWorker(stepperController=self.stepperController)
        self.moveWorker.start()

        self.robotCornerCoords = []
        self.humanCornerCoords = []
        self.cornersApplied = False
        self.originalCorners = np.float32([[0 ,0], [0, CAMERA_FRAME_HEIGHT - 1], [CAMERA_FRAME_WIDTH - 1, CAMERA_FRAME_HEIGHT - 1], [CAMERA_FRAME_WIDTH - 1, 0]])

        self.lastPosition = (0,0)
        self.currentPosition = (0,0)
        self.frameCounter = 0
        self.moveForward = True

    def exitApp(self):
        self.timer.stop()
        sys.exit()

    def applyCorners(self):
        if len(self.robotCornerCoords) == 2 and len(self.humanCornerCoords) == 2:
            self.logTextbox.append("Applied corners. Fitting image...")
            self.cornersApplied = True
        else:
            self.logTextbox.append("ERROR: Not all corners set. There must be 2 corners set for the robot side and 2 for the human player side. Use left click for the robot side and right click for the human side.")
            self.cornersApplied = False

    def resetCorners(self):
        self.logTextbox.append("Reset corners. Resetting image fit.")
        self.cornersApplied = False
        self.robotCornerCoords = []
        self.humanCornerCoords = []


    def getImageClickPos(self, event):
        x = event.pos().x()
        y = event.pos().y()
        # 1 is left click, 2 is right click
        mouseButton = event.button()
        if mouseButton == 1 and len(self.robotCornerCoords) < 2:
            self.robotCornerCoords.append((x,y))
        if mouseButton == 2 and len(self.humanCornerCoords) < 2:
            self.humanCornerCoords.append((x,y))       
        
        #print(f"Image clicked at X:{x}, Y:{y}")

    def sendMoveValues(self, x, y):
        self.moveWorker.set_values(x, y)

    def calibrate(self):
        # Add your calibration code here
        if self.stepperController is not None:
            self.logTextbox.append("Calibrating...")
            self.stepperController.calibrate()        
            self.isAtZero = True
        else:
            self.logTextbox.append("ERROR: Cannot calibrate. No Arduino found on " + STEPPER_COM_PORT + ".")

    def getMaxima(self):
        if self.stepperController is not None:
            x, y = self.stepperController.get_maxima()
            self.logTextbox.append(f"Maxima: X={x}, Y={y}")
        else:
            self.logTextbox.append("ERROR: Cannot get maxima. No Arduino found on " + STEPPER_COM_PORT + ".")

    def moveToPosition(self):
        if self.stepperController is not None:
            try:
                x = int(self.xCoordTextBox.toPlainText())
                y = int(self.yCoordTextBox.toPlainText())
                self.logTextbox.append("Moving to X=" + str(x) + ",Y=" + str(y))
                #self.stepperController.move_to_position(x, y)
                self.sendMoveValues(x, y)
            except ValueError:
                self.logTextbox.append("ERROR: X and/or Y value is not an integer. Cannot move to position.")
        else:
            self.logTextbox.append("ERROR: Cannot move to position. No Arduino found on " + STEPPER_COM_PORT + ".")

    def updateImages(self):
        #ret, frame = self.cap.read()
        ret, frame = self.camera.get_frame()
        if ret:
            if self.cornersApplied:                
                # If the corners are set then fit the image.
                # Corners have to be inputted counter clockwise.
                selectedCorners = np.float32([[self.robotCornerCoords[0][0], self.robotCornerCoords[0][1]],
                                            [self.robotCornerCoords[1][0], self.robotCornerCoords[1][1]],
                                            [self.humanCornerCoords[1][0], self.humanCornerCoords[1][1]],
                                            [self.humanCornerCoords[0][0], self.humanCornerCoords[0][1]]])

                # Calculate transformation matrix.
                matrix = cv2.getPerspectiveTransform(selectedCorners, self.originalCorners)
                # Warp the image.
                frame = cv2.warpPerspective(frame, matrix, (CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT))



            self.frameCounter = self.frameCounter + 1
            lowerBoundary = np.array([self.lowerHueSlider.value(), self.lowerSaturationSlider.value(), self.lowerValueSlider.value()])
            upperBoundary = np.array([self.upperHueSlider.value(), self.upperSaturationSlider.value(), self.upperValueSlider.value()])
            filteredFrame = filterFrameHSV(frame, lowerBoundary, upperBoundary)

            # Detect the puck and update UI values.
            (x, y), radius = detectPuck(filteredFrame, lowerBoundary, upperBoundary)
            frame = markPuckInFrame(frame, x, y, radius)

            self.puckXLabel.setText(str(f"X: {x:.1f}"))
            self.puckYLabel.setText(str(f"Y: {y:.1f}"))
            self.puckRadiusLabel.setText(str(f"Radius: {radius:.1f}"))            
            self.currentPosition = (x, y)
            vec = (x - self.lastPosition[0], y - self.lastPosition[1])
            self.puckVecLabel.setText(f"Vec: {vec[0]:.1f}, {vec[1]:.1f}")

            speed = vec[0] * vec[1]
            self.puckSpeedLabel.setText(f"Speed: {speed:.1f}")


            # Outputs the vector to the log. Only for debugging.
            # if (x,y) != (0,0):
            #     string = f"{self.lastPosition[0]},{self.lastPosition[1]},{self.currentPosition[0]},{self.currentPosition[1]}"
            #     self.logTextbox.append(string)


            pointA = (int(self.lastPosition[0]), int(self.lastPosition[1]))
            pointB = (int(self.currentPosition[0]), int(self.currentPosition[1]))

            angle = math.atan2(pointB[1] - pointA[1], pointB[0] - pointA[0])
            length = 500
            end_point = (int(pointA[0] + length*math.cos(angle)), int(pointA[1] + length*math.sin(angle)))
            #if vec[0] > 1 or vec[1] > 1:
            #if self.frameCounter > 5:
            self.lastPosition = (x, y)
            #self.frameCounter = 0
                
            cv2.line(frame, pointA, end_point, (0, 0, 255), 2)


            # Coordinates from table and camera are inverted.
            #
            # Camera:
            # |----WIDTH (X)---------|
            # |                      |
            # | HEIGHT (Y)           |
            # |                      |
            # |----------------------|
            #
            # Table:
            # |----Y-----------------|
            # |                      |
            # | X                    |
            # |                      |
            # |----------------------|

            

            if self.frameCounter > 5 and x != 0 and y != 0 and abs(speed) > 50:
                moveY, moveX = self.mapCoordinates(x, y, CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT, TABLE_MAX_Y, TABLE_MAX_X)
                cameraX, cameraY = self.mapCoordinates(moveY, moveX, TABLE_MAX_Y, TABLE_MAX_X, CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT)

                cv2.circle(frame, (int(cameraX), int(cameraY)), 10, (0, 255, 255), 2)

                # We only have half the field to work with so half the y.
                moveY = 500
                self.sendMoveValues(int(moveX), int(moveY))

                #self.logTextbox.append(f"Moving based on image to X={int(moveX)}, Y={moveY}...")
                self.frameCounter = 0

            if self.cornersApplied == False:
                # Draw the corners if they are set.
                for corner in self.robotCornerCoords:
                    cv2.circle(frame, (corner[0], corner[1]), 5, (255,255,0), 2)
                for corner in self.humanCornerCoords:
                    cv2.circle(frame, (corner[0], corner[1]), 5, (255,255,255), 2)


            self.updateImageFromFrame(self.cameraImageLabel, frame)            
            self.updateImageFromFrame(self.filteredImageLabel, filteredFrame)

    def mapCoordinates(self, x, y, maxWidthFrom, maxHeightFrom, maxWidthTo, maxHeightTo):
        xScale = maxWidthTo / maxWidthFrom
        yScale = maxHeightTo / maxHeightFrom
        x = x * xScale
        y = y * yScale
        return x, y

    def updateImageFromFrame(self, image, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, ch = frame.shape
        bytesPerLine = ch * width
        qtImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap(qtImg)
        image.setPixmap(pixmap)


        # filteredFrame = self.filterFrame(frame)
        # self.lowerBoundary = np.array([self.lowerHueSlider.value(), self.lowerSaturationSlider.value(), self.lowerValueSlider.value()])
        # self.upperBoundary = np.array([self.upperHueSlider.value(), self.upperSaturationSlider.value(), self.upperValueSlider.value()])
        # hsv = cv2.cvtColor(filteredFrame, cv2.COLOR_BGR2HSV)
        # mask = cv2.inRange(hsv, self.lowerBoundary, self.upperBoundary)
        # # We use medianBlur to get rid of so calles salt and pepper noise.
        # # If our mask gets other pixels besides the puck, we hope to eliminate them as best as possible with this "filter"
        # mask_blur = cv2.medianBlur(mask, 19)
        # contours, hierarchy = cv2.findContours(mask_blur, 1, 2)
        # if not contours:
        #     return ((0, 0), 0)
        # cnt = contours[0]
        # # We use minEnclosingCircle(), because if part of the puck is not detected (perhaps an arm above the puck), we might still be
        # # able to get the correct center
        # # We also tried cv2.HoughCircles as seen in "testHSV.py", but somehow it doesn't work.
        # # It might be faster than this method though. So if you are able to get the center with cv2.HoughCircles... give it a try
        # (x, y), radius = cv2.minEnclosingCircle(cnt)

        # #self.logTextbox.setText("X: " + str(x) + " | Y: " + str(y))

        # # Regular frame.
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # h, w, ch = frame.shape
        # bytes_per_line = ch * w
        # q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # pixmap = QPixmap(q_img)
        # self.cameraImageLabel.setPixmap(pixmap)

        # # Filtered frame.
        # filteredFrame = cv2.cvtColor(filteredFrame, cv2.COLOR_BGR2RGB)
        # h, w, ch = filteredFrame.shape
        # bytes_per_line = ch * w
        # q_img = QImage(filteredFrame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # pixmap = QPixmap(q_img)
        # self.filteredImageLabel.setPixmap(pixmap)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    splash = QSplashScreen(QPixmap("splash.png"))
    splash.show()
    main_window = MainWindow()
    splash.close()
    main_window.show()
    sys.exit(app.exec_())

