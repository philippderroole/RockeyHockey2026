import sys
import cv2
import math
import numpy as np
from datetime import datetime
from collections import deque
from PyQt5.QtCore import Qt, QTimer, QFile, QIODevice, QTextStream
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont
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
    QSlider,
)
from Constants import *
from Camera import Camera
from StepperController import *
from Processing.ProcessFrame import detectPuck, markInFrame, markRobotRectangle
from Processing.Line import Line


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rocky Hockey 2023")
        self.setWindowIcon(QIcon('RockyHockey2023Logo.png'))
        self.setupUI()
        # Create a timer to continuously update and process the camera image.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
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
        # Thread for communication with the arduino so the UI does not hang.
        self.moveWorker = MoveWorker(self.stepperController)
        self.moveWorker.start()
        # Coordinates to crop the camera image to fit the table.
        self.croppedTableCoords = [(TABLE_CORNER_TOP_LEFT_X, TABLE_CORNER_TOP_LEFT_Y),
                                   (TABLE_CORNER_TOP_RIGHT_X,
                                    TABLE_CORNER_TOP_RIGHT_Y),
                                   (TABLE_CORNER_BOTTOM_RIGHT_X,
                                    TABLE_CORNER_BOTTOM_RIGHT_Y),
                                   (TABLE_CORNER_BOTTOM_LEFT_X, TABLE_CORNER_BOTTOM_LEFT_Y)]
        # Is the image already cropped?
        self.cornersApplied = True
        # Original corner coordinates when cropping is reset.
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
        self.lastRobotPosition = (0, 0)
        self.currentRobotPosition = (0, 0)
        self.robotSpeed = 0
        self.puckSpeed = 0
        self.robotIsStopped = True
        self.robotWasStopped = True
        self.puckPositions = deque(maxlen=MAX_PUCK_POSITION_BUFFER)
        self.positionsSent = 0
        self.botActivated = False
        self.showDebugImages = True
        self.wasPuckGoingToRobot = False
        self.isPuckGoingToRobot = False
        self.predictionMade = False
        self.puckIsGoingLeft = False
        self.puckWasGoingLeft = False
        self.predictionLine = Line((0, 0), (0, 0))
        self.predictedPoints = []
        self.predictedPoint = (0, 0)
        self.collisionPoint = (0, 0)
        self.collisionPoints = []
        self.reflectionLine = Line((0, 0), (0, 0))
        self.puckCollides = False
        self.savedPoint = (0, 0)
        self.savedPoints = []
        self.lastMovePosition = (0, 0)
        self.wentBackToGoal = False
        self.attacked = False
        self.testTime = datetime.now()
        self.currentFrameTimestamp = datetime.now()
        self.lastFrameTimestamp = datetime.now()

    def setupUI(self):
        # Create a label to display the camera image.
        self.cameraImageLabel = QLabel(self)
        self.cameraImageLabel.setAlignment(Qt.AlignTop)
        self.cameraImageLabel.mousePressEvent = self.getImageClickPos
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
        self.setupPuckFilterUI()
        self.setupRobotFilterUI()
        # Create the right vertical box.
        self.vboxRight = QVBoxLayout()
        self.hboxImages = QHBoxLayout()
        self.hboxImages.addWidget(self.cameraImageLabel)
        self.vboxRight.addLayout(self.hboxImages)
        # Puck values.
        self.puckValuesHbox = QHBoxLayout()
        self.puckXLabel = QLabel(text="X: 0")
        self.puckYLabel = QLabel(text="Y: 0")
        self.puckRadiusLabel = QLabel(text="Radius: 0")
        self.puckSpeedLabel = QLabel(text="Speed: 0")
        self.puckValuesHbox.addWidget(QLabel(text="Puck Values: "))
        self.puckValuesHbox.addWidget(self.puckXLabel)
        self.puckValuesHbox.addWidget(self.puckYLabel)
        self.puckValuesHbox.addWidget(self.puckRadiusLabel)
        self.puckValuesHbox.addWidget(self.puckSpeedLabel)
        self.robotValuesHBox = QHBoxLayout()
        self.robotXLabel = QLabel(text="X: 0")
        self.robotYLabel = QLabel(text="Y: 0")
        self.robotRadiusLabel = QLabel(text="Radius: 0")
        self.robotSpeedLabel = QLabel(text="Speed: 0")
        self.robotValuesHBox.addWidget(QLabel(text="Robot Values: "))
        self.robotValuesHBox.addWidget(self.robotXLabel)
        self.robotValuesHBox.addWidget(self.robotYLabel)
        self.robotValuesHBox.addWidget(self.robotRadiusLabel)
        self.robotValuesHBox.addWidget(self.robotSpeedLabel)
        # Corner setting.
        self.cornersHBox = QHBoxLayout()
        self.cornersApplyButton = QPushButton("Apply Corners", self)
        self.cornersApplyButton.clicked.connect(self.applyCorners)
        self.cornersResetButton = QPushButton("Reset Corners", self)
        self.cornersResetButton.clicked.connect(self.resetCorners)
        self.cornersHBox.addWidget(self.cornersApplyButton)
        self.cornersHBox.addWidget(self.cornersResetButton)
        self.botSettingsHBox = QHBoxLayout()
        self.activateBotCheckBox = QCheckBox("Bot Active")
        self.botSettingsHBox.addWidget(self.activateBotCheckBox)
        self.activateBotCheckBox.clicked.connect(self.setBotState)
        self.activateBotCheckBox.setCheckState(Qt.CheckState.Unchecked)
        self.frameTimeLabel = QLabel("Frame Time: 0ms")
        self.botSettingsHBox.addWidget(self.frameTimeLabel)
        # Create the left vertical box.
        self.vboxLeft = QVBoxLayout()
        self.vboxLeft.addLayout(self.controlHorizontalBox)
        self.vboxLeft.addLayout(self.puckValuesHbox)
        self.vboxLeft.addLayout(self.filterVbox)
        self.vboxLeft.addLayout(self.robotValuesHBox)
        self.vboxLeft.addLayout(self.filterRobotVbox)
        self.vboxLeft.addLayout(self.cornersHBox)
        self.vboxLeft.addLayout(self.botSettingsHBox)
        self.vboxLeft.addWidget(self.logTextbox)
        self.vboxLeft.addWidget(self.exitButton)
        self.hboxMain = QHBoxLayout()
        # Create a central widget to hold the layouts
        self.CentralWidget = QWidget()
        self.CentralWidget.setLayout(self.hboxMain)

        # Set the central widget and add the horizontal layout to the bottom
        self.setCentralWidget(self.CentralWidget)
        self.hboxMain.addLayout(self.vboxLeft)
        self.hboxMain.addLayout(self.vboxRight)

    def setupRobotFilterUI(self):
        # Create the sliders for adjusting the filters.
        # We need the upper and lower bounds for Hue, Saturation and Value.
        self.lowerHueRobotSlider = QSlider(Qt.Horizontal)
        self.lowerSaturationRobotSlider = QSlider(Qt.Horizontal)
        self.lowerValueRobotSlider = QSlider(Qt.Horizontal)
        self.upperHueRobotSlider = QSlider(Qt.Horizontal)
        self.upperSaturationRobotSlider = QSlider(Qt.Horizontal)
        self.upperValueRobotSlider = QSlider(Qt.Horizontal)
        self.lowerHueRobotSlider.setMinimum(0)
        self.lowerHueRobotSlider.setMaximum(255)
        self.lowerSaturationRobotSlider.setMinimum(0)
        self.lowerSaturationRobotSlider.setMaximum(255)
        self.lowerValueRobotSlider.setMinimum(0)
        self.lowerValueRobotSlider.setMaximum(255)
        self.upperHueRobotSlider.setMinimum(0)
        self.upperHueRobotSlider.setMaximum(255)
        self.upperSaturationRobotSlider.setMinimum(0)
        self.upperSaturationRobotSlider.setMaximum(255)
        self.upperValueRobotSlider.setMinimum(0)
        self.upperValueRobotSlider.setMaximum(255)
        self.lowerHueRobotSlider.setValue(CAMERA_ROBOT_LOWER_HUE)
        self.lowerSaturationRobotSlider.setValue(CAMERA_ROBOT_LOWER_SATURATION)
        self.lowerValueRobotSlider.setValue(CAMERA_ROBOT_LOWER_VALUE)
        self.upperHueRobotSlider.setValue(CAMERA_ROBOT_UPPER_HUE)
        self.upperSaturationRobotSlider.setValue(CAMERA_ROBOT_UPPER_SATURATION)
        self.upperValueRobotSlider.setValue(CAMERA_ROBOT_UPPER_VALUE)
        self.lowerHueRobotLabel = QLabel(str(self.lowerHueRobotSlider.value()))
        self.lowerSaturationRobotLabel = QLabel(
            str(self.lowerSaturationRobotSlider.value()))
        self.lowerValueRobotLabel = QLabel(
            str(self.lowerValueRobotSlider.value()))
        self.upperHueRobotLabel = QLabel(str(self.upperHueRobotSlider.value()))
        self.upperSaturationRobotLabel = QLabel(
            str(self.upperSaturationRobotSlider.value()))
        self.upperValueRobotLabel = QLabel(
            str(self.upperValueRobotSlider.value()))

        self.lowerHueRobotSlider.valueChanged.connect(
            lambda value: self.lowerHueRobotLabel.setText(str(value))
        )
        self.lowerSaturationRobotSlider.valueChanged.connect(
            lambda value: self.lowerSaturationRobotLabel.setText(str(value))
        )
        self.lowerValueRobotSlider.valueChanged.connect(
            lambda value: self.lowerValueRobotLabel.setText(str(value))
        )
        self.upperHueRobotSlider.valueChanged.connect(
            lambda value: self.upperHueRobotLabel.setText(str(value))
        )
        self.upperSaturationRobotSlider.valueChanged.connect(
            lambda value: self.upperSaturationRobotLabel.setText(str(value))
        )
        self.upperValueRobotSlider.valueChanged.connect(
            lambda value: self.upperValueRobotLabel.setText(str(value))
        )

        self.lowerHueRobotHbox = QHBoxLayout()
        self.lowerSaturationRobotHbox = QHBoxLayout()
        self.lowerValueRobotHbox = QHBoxLayout()
        self.upperHueRobotHbox = QHBoxLayout()
        self.upperSaturationRobotHbox = QHBoxLayout()
        self.upperValueRobotHbox = QHBoxLayout()

        self.lowerHueRobotLabelText = QLabel(text="Lower Hue: ")
        self.lowerSaturationRobotLabelText = QLabel(text="Lower Sat: ")
        self.lowerValueRobotLabelText = QLabel(text="Lower Val: ")
        self.upperHueRobotLabelText = QLabel(text="Upper Hue: ")
        self.upperSaturationRobotLabelText = QLabel(text="Upper Sat: ")
        self.upperValueRobotLabelText = QLabel(text="Upper Val: ")

        self.lowerHueRobotLabelText.setFixedWidth(100)
        self.lowerSaturationRobotLabelText.setFixedWidth(100)
        self.lowerValueRobotLabelText.setFixedWidth(100)
        self.upperHueRobotLabelText.setFixedWidth(100)
        self.upperSaturationRobotLabelText.setFixedWidth(100)
        self.upperValueRobotLabelText.setFixedWidth(100)

        self.lowerHueRobotLabel.setFixedWidth(30)
        self.lowerSaturationRobotLabel.setFixedWidth(30)
        self.lowerValueRobotLabel.setFixedWidth(30)
        self.upperHueRobotLabel.setFixedWidth(30)
        self.upperSaturationRobotLabel.setFixedWidth(30)
        self.upperValueRobotLabel.setFixedWidth(30)

        self.lowerHueRobotHbox.addWidget(self.lowerHueRobotLabelText)
        self.lowerHueRobotHbox.addWidget(self.lowerHueRobotLabel)
        self.lowerHueRobotHbox.addWidget(self.lowerHueRobotSlider)

        self.lowerSaturationRobotHbox.addWidget(
            self.lowerSaturationRobotLabelText)
        self.lowerSaturationRobotHbox.addWidget(self.lowerSaturationRobotLabel)
        self.lowerSaturationRobotHbox.addWidget(
            self.lowerSaturationRobotSlider)

        self.lowerValueRobotHbox.addWidget(self.lowerValueRobotLabelText)
        self.lowerValueRobotHbox.addWidget(self.lowerValueRobotLabel)
        self.lowerValueRobotHbox.addWidget(self.lowerValueRobotSlider)

        self.upperHueRobotHbox.addWidget(self.upperHueRobotLabelText)
        self.upperHueRobotHbox.addWidget(self.upperHueRobotLabel)
        self.upperHueRobotHbox.addWidget(self.upperHueRobotSlider)

        self.upperSaturationRobotHbox.addWidget(
            self.upperSaturationRobotLabelText)
        self.upperSaturationRobotHbox.addWidget(self.upperSaturationRobotLabel)
        self.upperSaturationRobotHbox.addWidget(
            self.upperSaturationRobotSlider)

        self.upperValueRobotHbox.addWidget(self.upperValueRobotLabelText)
        self.upperValueRobotHbox.addWidget(self.upperValueRobotLabel)
        self.upperValueRobotHbox.addWidget(self.upperValueRobotSlider)

        self.filterRobotVbox = QVBoxLayout()
        self.filterRobotVbox.addLayout(self.lowerHueRobotHbox)
        self.filterRobotVbox.addLayout(self.lowerSaturationRobotHbox)
        self.filterRobotVbox.addLayout(self.lowerValueRobotHbox)
        self.filterRobotVbox.addLayout(self.upperHueRobotHbox)
        self.filterRobotVbox.addLayout(self.upperSaturationRobotHbox)
        self.filterRobotVbox.addLayout(self.upperValueRobotHbox)

    def setupPuckFilterUI(self):
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
        self.lowerSaturationLabel = QLabel(
            str(self.lowerSaturationSlider.value()))
        self.lowerValueLabel = QLabel(str(self.lowerValueSlider.value()))
        self.upperHueLabel = QLabel(str(self.upperHueSlider.value()))
        self.upperSaturationLabel = QLabel(
            str(self.upperSaturationSlider.value()))
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
        self.lowerSaturationLabelText = QLabel(text="Lower Sat: ")
        self.lowerValueLabelText = QLabel(text="Lower Val: ")
        self.upperHueLabelText = QLabel(text="Upper Hue: ")
        self.upperSaturationLabelText = QLabel(text="Upper Sat: ")
        self.upperValueLabelText = QLabel(text="Upper Val: ")
        self.lowerHueLabelText.setFixedWidth(100)
        self.lowerSaturationLabelText.setFixedWidth(100)
        self.lowerValueLabelText.setFixedWidth(100)
        self.upperHueLabelText.setFixedWidth(100)
        self.upperSaturationLabelText.setFixedWidth(100)
        self.upperValueLabelText.setFixedWidth(100)
        self.lowerHueLabel.setFixedWidth(30)
        self.lowerSaturationLabel.setFixedWidth(30)
        self.lowerValueLabel.setFixedWidth(30)
        self.upperHueLabel.setFixedWidth(30)
        self.upperSaturationLabel.setFixedWidth(30)
        self.upperValueLabel.setFixedWidth(30)
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

    def closeEvent(self, event):
        # Let the window close.
        event.accept()
        self.exitApp()

    def exitApp(self):
        self.timer.stop()
        self.camera.stop()
        sys.exit()

    def setBotState(self):
        if self.activateBotCheckBox.checkState() == Qt.CheckState.Checked:
            self.botActivated = True
        else:
            self.botActivated = False

    def applyCorners(self):
        if len(self.croppedTableCoords) == 4:
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
        self.croppedTableCoords = []

    def getImageClickPos(self, event):
        # The Camera image is double the size of the debug window image.
        x = event.pos().x()
        y = event.pos().y()
        print(f"Clicked x:{x}, y:{y}")
        # 1 is left click, 2 is right click
        mouseButton = event.button()
        if mouseButton == 1 and len(self.croppedTableCoords) < 4:
            self.croppedTableCoords.append((x, y))
        elif mouseButton == 2:
            moveX, moveY = self.mapCoordinates(
                x,
                y,
                CAMERA_FRAME_HEIGHT,
                CAMERA_FRAME_ROBOT_MAX_Y,
                TABLE_MAX_X,
                TABLE_MAX_Y,
            )
            moveX = TABLE_MAX_X - moveX
            self.logTextbox.append(
                f"Clicked on {x},{y} in Image and moving to {int(moveX)},{int(moveY)}.")
            self.sendMoveValues(moveX, moveY)

    def sendMoveValues(self, x, y):
        # Do scaling.
        offset = (x - (TABLE_MAX_X / 2)) / 9
        x += offset
        y -= 50

        if abs(x - self.lastMovePosition[0]) < 50 and abs(y - self.lastMovePosition[1]) < 50:
            return

        self.lastMovePosition = (x, y)

        # if self.botActivated:
        self.positionsSent += 1
        # print(f"Sending {self.positionsSent} (X:{int(x)}, Y:{int(y)})")
        self.moveWorker.set_values(MoveType.NORMAL, x, y)

    def calibrate(self):
        # Add your calibration code here
        if self.stepperController is not None:
            self.logTextbox.append("Calibrating...")
            self.moveWorker.set_values(MoveType.CALIBRATE, 0, 0)
            self.isAtZero = True
            self.sendMoveValues((TABLE_MAX_X / 2), 200)
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
                self.logTextbox.append(
                    "Moving to X=" + str(x) + ",Y=" + str(y))
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
    def update(self):
        # Check if new camera image is available
        if self.camera.new_frame:
            frame = self.initializeCamera()
            x, y, radius, robotX, robotY, robotRadius = self.defineBoundaries(frame)

            # TODO: Robot detection is not that stable
            # Check detected robot radius (if robot was not recognised correctly set invalid values)
            if robotRadius < 10 or robotRadius > 50:
                robotX = -1
                robotY = -1
                robotRadius = -1
                self.robotSpeed = -1

            self.currentPosition = (x, y)
            self.currentRobotPosition = (robotX, robotY)

            # Calculate robot and puck speed
            self.puckSpeed = math.sqrt((self.currentPosition[0] - self.lastPosition[0]) ** 2 + (
                    self.currentPosition[1] - self.lastPosition[1]) ** 2)
            self.robotSpeed = math.sqrt((self.currentRobotPosition[0] - self.lastRobotPosition[0]) ** 2 + (
                    self.currentRobotPosition[1] - self.lastRobotPosition[1]) ** 2)
            self.robotIsStopped = self.robotSpeed <= 1 or self.robotSpeed == -1

            frame = self.updatePreCalculationUi(frame, x, y, radius, robotX, robotY, robotRadius)

            self.isPuckGoingToRobot = self.currentPosition[1] < self.lastPosition[1] and (
                    self.lastPosition[1] - self.currentPosition[1]) > 1
            self.puckIsGoingLeft = self.currentPosition[0] < self.lastPosition[0] and (
                    self.lastPosition[0] - self.currentPosition[0]) > 5
            
            # Check if puck is currently moving to the robot and if it also moved towards the robot during the last update
            if self.isPuckGoingToRobot and self.wasPuckGoingToRobot:

                #check if new prediciton is needed (because reflection has taken place)
                if(len(self.predictedPoints) >= 1 and self.lastPosition[1] < self.collisionPoints[0][1]):
                    self.predictionMade = False

                if not self.predictionMade:
                    self.puckCollides = False

                    #reset saved points
                    self.savedPoints = []
                    self.predictedPoints = []
                    self.collisionPoints = []

                    # Draw line between current and last puck position
                    self.predictionLine = Line(self.lastPosition, self.currentPosition)

                    self.savedPoint = self.currentPosition

                    try:
                        if self.predictionLine.get_m() is not None:
                            i = 0
                            while i < 5:
                                # Check if puck collides with a wall
                                if self.predictionLine.get_angle() >= 0:  # left edge
                                    self.collisionPoint = (
                                        0 + (radius / 2), self.predictionLine.get_y(0 + (radius / 2)))
                                    self.puckCollides = True
                                else:  # right edge
                                    self.collisionPoint = (
                                        CAMERA_FRAME_HEIGHT - (radius / 2),
                                        self.predictionLine.get_y(CAMERA_FRAME_HEIGHT - (radius / 2)))
                                    self.puckCollides = True
                                
                                #save things for UI #1
                                self.savedPoints.append(self.savedPoint)
                                self.collisionPoints.append(self.collisionPoint)

                                # If puck collides with wall calculate the reflection point
                                if self.puckCollides and self.collisionPoint[1] > 0:
                                    self.reflectionLine = Line(
                                        self.collisionPoint, None, (-1 * self.predictionLine.get_m() * 2.5))
                                    print(
                                        f"Reflection line m={self.reflectionLine.get_m()}")
                                    self.predictedPoint = (self.reflectionLine.get_x(
                                        DEFENSIVE_LINE), DEFENSIVE_LINE)
                                    self.predictionMade = True
                                    self.wentBackToGoal = False
                                    self.attacked = False
                                else:
                                    self.predictedPoint = (
                                        self.predictionLine.get_x(DEFENSIVE_LINE), DEFENSIVE_LINE)
                                    self.predictionMade = True
                                    self.wentBackToGoal = False
                                    self.attacked = False
                                    break
                               #save thigns for ui #2 reflection only
                                self.predictedPoints.append(self.predictedPoint)

                                self.predictionLine = self.reflectionLine
                                self.savedPoint = self.currentPosition
                                # frame = self.updatePostCalculationUi(frame)
                                i += 1

                            
                            # Check if predicted puck position is valid 
                            if 50 < self.predictedPoint[0] < (CAMERA_FRAME_HEIGHT - 50):
                                # Calculate robot movement to the predicted puck position
                                moveX, moveY = self.mapCoordinates(
                                    self.predictedPoint[0],
                                    self.predictedPoint[1],
                                    CAMERA_FRAME_HEIGHT,
                                    CAMERA_FRAME_ROBOT_MAX_Y,
                                    TABLE_MAX_X,
                                    TABLE_MAX_Y,
                                )
                                moveX = TABLE_MAX_X - moveX

                                # If bot is activated move to the calculated position
                                if self.botActivated:
                                    self.logTextbox.append(
                                        f"Move To: X={moveX:.0f}, Y={moveY:.0f}")
                                    self.positionsSent += 1
                                    self.sendMoveValues(moveX, moveY)

                                    #move towards puck if last reflection
                                    if(self.collisionPoints[0][1] <= 0):
                                        self.positionsSent += 1
                                        moveX, moveY = self.mapCoordinates(
                                            self.predictedPoint[0],
                                            self.predictedPoint[1]+200,
                                            CAMERA_FRAME_HEIGHT,
                                            CAMERA_FRAME_ROBOT_MAX_Y,
                                            TABLE_MAX_X,
                                            TABLE_MAX_Y,
                                        )
                                        moveX = TABLE_MAX_X - moveX
                                        self.sendMoveValues(moveX, moveY)

                    except:
                        pass
            
            # Executed if the puck isn't moving to the robot or didn't move to the robot in the previous update 
            else:
                self.predictionMade = False

                # Executed if the robot isn't in the goal
                if not self.wentBackToGoal:
                    self.wentBackToGoal = True

                    # Calculate robot movements to goal
                    moveX, moveY = self.mapCoordinates(
                        (CAMERA_FRAME_HEIGHT / 2),
                        DEFENSIVE_LINE,
                        CAMERA_FRAME_HEIGHT,
                        CAMERA_FRAME_ROBOT_MAX_Y,
                        TABLE_MAX_X,
                        TABLE_MAX_Y,
                    )

                    # If bot is activated move to the calculated position
                    if self.botActivated:
                        self.sendMoveValues(int(moveX), int(moveY))

            self.wasPuckGoingToRobot = self.isPuckGoingToRobot
            self.puckWasGoingLeft = self.puckIsGoingLeft
            self.lastPosition = self.currentPosition
            self.lastRobotPosition = self.currentRobotPosition
            self.robotWasStopped = self.robotIsStopped

            frame = self.updatePostCalculationUi(frame)
            frame = self.updateFrameTime
    

    def updatePostCalculationUi(self, frame):
        if self.predictionMade and self.predictionLine.get_m() is not None:
            if self.showDebugImages:
                # Draw predicted and current puck position
                cv2.circle(frame, (int(self.predictedPoint[0]), int(self.predictedPoint[1])),
                           5, (255, 0, 255), -1)
                cv2.circle(frame, (int(self.savedPoint[0]),
                                   int(self.savedPoint[1])), 5, (0, 0, 0), -1)
                
                # Draw predicted line
                if not self.puckCollides:
                    cv2.line(
                        frame,
                        (int(self.currentPosition[0]),
                         int(self.currentPosition[1])),
                        (int(self.predictedPoint[0]), int(
                            self.predictedPoint[1])),
                        (255, 0, 0),
                        thickness=2,
                        lineType=4,
                    )
                    cv2.line(
                        frame,
                        (int(self.savedPoint[0]),
                         int(self.savedPoint[1])),
                        (int(self.predictedPoint[0]), int(
                            self.predictedPoint[1])),
                        (255, 0, 0),
                        thickness=2,
                        lineType=4,
                    )

            # Draw prediction line before collision
            cv2.line(frame,
                     (int(self.savedPoints[0][0]), int(
                         self.savedPoints[0][1])),
                     (int(self.collisionPoints[0][0]), int(
                         self.collisionPoints[0][1])),
                     (255, 0, 0), thickness=2, lineType=4)
            # Executed if the puck collides with a wall
            if self.puckCollides:
                if len(self.collisionPoints) > 0:
                    for i in range(len(self.predictedPoints)):
                        # Draw collision point
                        cv2.circle(frame, (int(self.collisionPoints[i][0]), int(self.collisionPoints[i][1])),
                                   10, (255, 255, 255), -1)
                        # Draw reflection line after collision
                        cv2.line(frame,
                                 (int(self.collisionPoints[i][0]), int(
                                     self.collisionPoints[i][1])),
                                 (int(self.predictedPoints[i][0]), int(
                                     self.predictedPoints[i][1])),
                                 (255, 255, 0), thickness=2, lineType=4)
                    
        if self.showDebugImages:
            self.updateImageFromFrame(self.cameraImageLabel, frame)
        
        return frame
    
    def updateFrameTime(self):
     # Calculate frame time and FPS
        frameTimeMs = (self.currentFrameTimestamp -
                       self.lastFrameTimestamp).microseconds / 1000
        self.lastFrameTimestamp = self.currentFrameTimestamp
        fps = 1000 / frameTimeMs
        self.frameTimeLabel.setText(
            f"Frame Time: {frameTimeMs:.0f}ms ({fps:.0f} FPS)")

    def updatePreCalculationUi(self, frame, x, y, radius, robotX, robotY, robotRadius):
        # Draw outlines of puck, robot and playfield in the camera image
        frame = markInFrame(frame, x, y, radius, FRAME_PUCK_OUTLINE_COLOR)
        if robotX != -1 and robotY != -1 and robotRadius != -1:
            frame = markInFrame(frame, robotX, robotY, robotRadius, FRAME_ROBOT_OUTLINE_COLOR)
        frame = markRobotRectangle(frame)

        # Update puck and robot values in the UI
        self.puckXLabel.setText(str(f"X: {x:.0f}"))
        self.puckYLabel.setText(str(f"Y: {y:.0f}"))
        self.puckRadiusLabel.setText(str(f"Radius: {radius:.0f}"))
        self.puckSpeedLabel.setText(str(f"Speed: {self.puckSpeed:.1f}"))

        self.robotXLabel.setText(str(f"X: {robotX:.0f}"))
        self.robotYLabel.setText(str(f"Y: {robotY:.0f}"))
        self.robotRadiusLabel.setText(str(f"Radius: {robotRadius:.0f}"))
        self.robotSpeedLabel.setText(str(f"Speed: {self.robotSpeed:.1f}"))

        return frame


    def defineBoundaries(self, frame):
        # Lower and upper color spectrum for the puck
        lowerBoundary = np.array([
                self.lowerHueSlider.value(),
                self.lowerSaturationSlider.value(),
                self.lowerValueSlider.value(),
            ])
        upperBoundary = np.array([
                self.upperHueSlider.value(),
                self.upperSaturationSlider.value(),
                self.upperValueSlider.value(),
            ])
        
        # TODO: Improve robot detection 
        # Lower and upper color spectrum for the robot 
        robotLowerBoundary = np.array([
                self.lowerHueRobotSlider.value(),
                self.lowerSaturationRobotSlider.value(),
                self.lowerValueRobotSlider.value(),
            ])
        robotUpperBoundary = np.array([
                self.upperHueRobotSlider.value(),
                self.upperSaturationRobotSlider.value(),
                self.upperValueRobotSlider.value(),
            ])
        
        # Detect the puck/robot in the camera image
        (x, y), radius = detectPuck(
                frame, lowerBoundary, upperBoundary)
        (robotX, robotY), robotRadius = detectPuck(
                frame, robotLowerBoundary, robotUpperBoundary
            )
        
        return x,y,radius,robotX,robotY,robotRadius


    def initializeCamera(self):
        self.currentFrameTimestamp = datetime.now()

        # Current camera image
        frame = self.camera.get_current_frame()

        # Check if corners of the camera image have been set
        if self.cornersApplied:
            # Input corners clockwise
            selectedCorners = np.float32(
                    [
                        [self.croppedTableCoords[0][0],
                         self.croppedTableCoords[0][1]],
                        [self.croppedTableCoords[1][0],
                         self.croppedTableCoords[1][1]],
                        [self.croppedTableCoords[2][0],
                         self.croppedTableCoords[2][1]],
                        [self.croppedTableCoords[3][0],
                         self.croppedTableCoords[3][1]],
                    ]
                )

            # Calculate transformation matrix (to apply a perspective transformation to the image)
            matrix = cv2.getPerspectiveTransform(selectedCorners, self.originalCorners)
            
            # Apply perspective transformation
            frame = cv2.warpPerspective(frame, matrix, (CAMERA_FRAME_HEIGHT, CAMERA_FRAME_WIDTH))
        
        # Select corners of the camera image if they aren't set
        if not self.cornersApplied:
            for corner in self.croppedTableCoords:
                cv2.circle(frame, (corner[0], corner[1]), 5, (255, 255, 255), 2)

        self.frameCounter = self.frameCounter + 1

        return frame


    def mapCoordinates(
            self, x, y, maxWidthFrom, maxHeightFrom, maxWidthTo, maxHeightTo
    ):
        xScale = maxWidthTo / maxWidthFrom
        yScale = maxHeightTo / maxHeightFrom
        x = x * xScale
        y = y * yScale
        return x, y

    def updateImageFromFrame(self, image, frame):
        # Resize to GUI size.
        # frame = cv2.resize(frame, (DEBUG_WINDOW_FRAME_HEIGHT, DEBUG_WINDOW_FRAME_WIDTH))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, ch = frame.shape
        bytesPerLine = ch * width
        qtImg = QImage(frame.data, width, height,
                       bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap(qtImg)
        image.setPixmap(pixmap)


if __name__ == "__main__":
    cv2.ocl.setUseOpenCL(True)
    app = QApplication(sys.argv)
    # app.setStyleSheet(qdarkstyle.load_stylesheet())
    splash = QSplashScreen(QPixmap("splash.png"))
    splash.show()
    main_window = MainWindow()
    splash.close()

    # Set style with stylesheet.
    stream = QFile("style.qss")
    stream.open(QIODevice.ReadOnly)
    main_window.setStyleSheet(QTextStream(stream).readAll())

    font = QFont("Courier New")
    app.setFont(font)

    main_window.show()
    sys.exit(app.exec_())
