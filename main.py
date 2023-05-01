# from StepperController import StepperController
# from Camera import Camera
# from UserInterface import UserInterface
# #controller = StepperController("COM4", 115200)
# camera = Camera(1, 60)
# userInterface = UserInterface(None, camera)

import sys
import cv2
import numpy as np
import qdarkstyle
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMainWindow, QLabel, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QSlider

from Constants import *
from Camera import Camera
from StepperController import StepperController
from Processing.ProcessFrame import filterFrameHSV

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rocky Hockey 2023")

        # Create a label to display the camera image.
        self.cameraImageLabel = QLabel(self)
        self.cameraImageLabel.setAlignment(Qt.AlignCenter)

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

        self.xCoordTextBox = QTextEdit()
        self.xCoordTextBox.setFixedHeight(25)
        self.xCoordTextBox.setText("0")
        self.yCoordTextBox = QTextEdit()
        self.yCoordTextBox.setFixedHeight(25)
        self.yCoordTextBox.setText("0")

        self.controlHorizontalBox = QHBoxLayout()
        self.controlHorizontalBox.addWidget(self.calibrateButton)
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



        # Create the left vertical box.
        self.vboxLeft = QVBoxLayout()
        self.vboxLeft.addLayout(self.controlHorizontalBox)        
        self.vboxLeft.addWidget(QLabel(text="Adjust filters"))
        self.vboxLeft.addLayout(self.filterVbox)
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
        self.camera = Camera()
        self.stepperController = None
        # Stepper Controller
        try:
            self.stepperController = StepperController(STEPPER_COM_PORT, STEPPER_BAUDRATE)        
        except Exception:
            self.logTextbox.append("ERROR: No Arduino found on " + STEPPER_COM_PORT + ".")

        self.showMaximized()

    def exitApp(self):
        self.timer.stop()
        sys.exit()

    def calibrate(self):
        # Add your calibration code here
        if self.stepperController is not None:
            self.logTextbox.append("Calibrating...")
            self.stepperController.calibrate()        
            self.isAtZero = True
        else:
            self.logTextbox.append("ERROR: Cannot calibrate. No Arduino found on " + STEPPER_COM_PORT + ".")

    def moveToPosition(self):
        if self.stepperController is not None:
            try:
                x = int(self.xCoordTextBox.toPlainText())
                y = int(self.yCoordTextBox.toPlainText())
                self.logTextbox.append("Moving to X=" + str(x) + ",Y=" + str(y))
                self.stepperController.move(x, y)
            except ValueError:
                self.logTextbox.append("ERROR: X and/or Y value is not an integer. Cannot move to position.")
        else:
            self.logTextbox.append("ERROR: Cannot move to position. No Arduino found on " + STEPPER_COM_PORT + ".")

    def updateImages(self):
        #ret, frame = self.cap.read()
        ret, frame = self.camera.get_frame()
        if ret:
            lowerBoundary = np.array([self.lowerHueSlider.value(), self.lowerSaturationSlider.value(), self.lowerValueSlider.value()])
            upperBoundary = np.array([self.upperHueSlider.value(), self.upperSaturationSlider.value(), self.upperValueSlider.value()])
            filteredFrame = filterFrameHSV(frame, lowerBoundary, upperBoundary)
            self.updateImageFromFrame(self.cameraImageLabel, frame)            
            self.updateImageFromFrame(self.filteredImageLabel, filteredFrame)

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

