import sys
import socket
import json
import threading
import cv2
import math
import numpy as np
import time
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
    QTabWidget,
    QSpinBox,
)
from Constants import *
from StepperController import *
from Processing.Line import Line
from Strategy import RobotController
from DataModel import model


class CameraReceiver(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._lock = threading.Lock()
        self._latest = {"puck_x": -1, "puck_y": -1, "robot_x": -1, "robot_y": -1, "timestamp": None}
        self._new_data = False

    @property
    def new_data(self):
        with self._lock:
            return self._new_data

    def get_latest(self):
        with self._lock:
            self._new_data = False
            return self._latest.copy()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 0))
        sock.connect((CAMERA_DETECTOR_HOST, CAMERA_DETECTOR_PORT))
        sock.send(b"subscribe")
        sock.settimeout(1.0)
        while True:
            try:
                data = sock.recv(65535)
                message = json.loads(data.decode("utf-8"))
                puck_x, puck_y, robot_x, robot_y = -1, -1, -1, -1
                for detection in message.get("detections", []):
                    name = detection.get("target_name", "")
                    if name == "Puck":
                        puck_x = detection["x"]
                        puck_y = detection["y"]
                        puck_x, puck_y = self.map_camera_coordinates(puck_x, puck_y)
                    elif name == "Robot":
                        robot_x = detection["x"]
                        robot_y = detection["y"]
                        robot_x, robot_y = self.map_camera_coordinates(robot_x, robot_y)
                with self._lock:
                    self._latest = {
                        "puck_x": puck_x,
                        "puck_y": puck_y,
                        "robot_x": robot_x,
                        "robot_y": robot_y,
                        "timestamp": datetime.now(),
                    }
                    self._new_data = True
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Camera receiver error: {e}")

    def map_camera_coordinates(self, cam_x, cam_y):
        try:
            self.cam_x_offset = -32
            self.cam_y_offset = -95

            cam_x = cam_x + self.cam_x_offset
            cam_y = cam_y + self.cam_y_offset

            cam_x = self.map_range(cam_x, 0, 269, 0, TABLE_MAX_X)
            cam_y = self.map_range(cam_y, 0, 326, 0, TABLE_MAX_Y)

            return cam_x, cam_y
        except Exception as e:
            print(f"Camera receiver error: {e}")

    def map_range(self,value, from_min, from_max, to_min, to_max):
        return (value - from_min) / (from_max - from_min) * (to_max - to_min) + to_min

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rocky Hockey 2026")
        self.setWindowIcon(QIcon("RockyHockey2023Logo.png"))
        self.setupUI()
        self.cameraReceiver = CameraReceiver()
        self.cameraReceiver.start()
        self.controller = RobotController(self.sendMoveValues)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.preUpdate)
        self.timer.start(1)
        self.stepperController = None
        try:
            self.stepperController = StepperController(STEPPER_COM_PORT, STEPPER_BAUDRATE)
            self.stepperController.connect()
            self.stepperController.calibrate()
            self.stepperController.move_to_position(HOME_POSITION_X, HOME_POSITION_Y)
        except Exception:
            self.logTextbox.append("ERROR: No Arduino found on " + STEPPER_COM_PORT + ".")
            self.stepperController = None
        if self.stepperController is not None:
            self.calibrate()
        self.data = model
        self.setFocusPolicy(Qt.StrongFocus)

    def setupUI(self):
        self.cameraImageLabel = QLabel(self)
        self.cameraImageLabel.setAlignment(Qt.AlignTop)
        self.cameraImageLabel.mousePressEvent = self.getImageClickPos

        self.logTextbox = QTextEdit(self)
        self.logTextbox.setReadOnly(True)

        self.exitButton = QPushButton("Exit", self)
        self.exitButton.clicked.connect(self.exitApp)
        self.calibrateButton = QPushButton("Calibrate", self)
        self.calibrateButton.clicked.connect(self.calibrate)
        self.moveToPositionButton = QPushButton("Move To Position", self)
        self.moveToPositionButton.clicked.connect(self.moveToPosition)
        self.getMaximaButton = QPushButton("Get Maxima", self)
        self.getMaximaButton.clicked.connect(self.getMaxima)

        self.xCoordTextBox = QSpinBox()
        self.xCoordTextBox.setRange(0, 2000)
        self.xCoordTextBox.setSingleStep(10)
        self.xCoordTextBox.setFixedHeight(25)
        self.xCoordTextBox.setStyleSheet("color: white; background-color: #333; border: 1px solid #555;")

        self.yCoordTextBox = QSpinBox()
        self.yCoordTextBox.setRange(0, 2000)
        self.yCoordTextBox.setSingleStep(10)
        self.yCoordTextBox.setFixedHeight(25)
        self.yCoordTextBox.setStyleSheet("color: white; background-color: #333; border: 1px solid #555;")

        self.controlHorizontalBox = QHBoxLayout()
        self.controlHorizontalBox.addWidget(self.calibrateButton)
        self.controlHorizontalBox.addWidget(self.getMaximaButton)
        self.controlHorizontalBox.addWidget(self.moveToPositionButton)
        self.controlHorizontalBox.addWidget(QLabel(text="X"))
        self.controlHorizontalBox.addWidget(self.xCoordTextBox)
        self.controlHorizontalBox.addWidget(QLabel(text="Y"))
        self.controlHorizontalBox.addWidget(self.yCoordTextBox)

        self.botSettingsHBox = QHBoxLayout()
        self.activateBotCheckBox = QCheckBox("Bot Active")
        self.activateBotCheckBox.clicked.connect(self.setBotState)
        self.activateBotCheckBox.setCheckState(Qt.CheckState.Unchecked)
        self.frameTimeLabel = QLabel("Frame Time: 0ms")
        self.botSettingsHBox.addWidget(self.activateBotCheckBox)
        self.botSettingsHBox.addWidget(self.frameTimeLabel)

        self.puckValuesHbox = QHBoxLayout()
        self.puckXLabel = QLabel(text="X: 0")
        self.puckYLabel = QLabel(text="Y: 0")
        self.puckSpeedLabel = QLabel(text="Speed: 0")
        self.puckValuesHbox.addWidget(QLabel(text="Puck: "))
        self.puckValuesHbox.addWidget(self.puckXLabel)
        self.puckValuesHbox.addWidget(self.puckYLabel)
        self.puckValuesHbox.addWidget(self.puckSpeedLabel)

        self.robotValuesHBox = QHBoxLayout()
        self.robotXLabel = QLabel(text="X: 0")
        self.robotYLabel = QLabel(text="Y: 0")
        self.robotValuesHBox.addWidget(QLabel(text="Robot: "))
        self.robotValuesHBox.addWidget(self.robotXLabel)
        self.robotValuesHBox.addWidget(self.robotYLabel)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; background: #222; }
            QTabBar::tab { background: #333; color: #ddd; padding: 10px; border: 1px solid #444; }
            QTabBar::tab:selected { background: #555; color: white; border-bottom: none; }
            QWidget { background-color: #222; color: #eee; }
        """)

        self.tabControls = QWidget()
        self.tabControlsLayout = QVBoxLayout()
        self.tabControlsLayout.addLayout(self.controlHorizontalBox)
        self.tabControlsLayout.addLayout(self.puckValuesHbox)
        self.tabControlsLayout.addLayout(self.robotValuesHBox)
        self.tabControlsLayout.addLayout(self.botSettingsHBox)
        self.tabControlsLayout.addWidget(self.logTextbox)
        self.tabControlsLayout.addWidget(self.exitButton)
        self.tabControls.setLayout(self.tabControlsLayout)

        self.tabs.addTab(self.tabControls, "Controls & Log")

        self.vboxLeft = QVBoxLayout()
        self.vboxLeft.addWidget(self.tabs)

        self.vboxRight = QVBoxLayout()
        self.hboxImages = QHBoxLayout()
        self.hboxImages.addWidget(self.cameraImageLabel)
        self.vboxRight.addLayout(self.hboxImages)

        self.hboxMain = QHBoxLayout()
        self.CentralWidget = QWidget()
        self.CentralWidget.setLayout(self.hboxMain)
        self.setCentralWidget(self.CentralWidget)

        self.hboxMain.addLayout(self.vboxLeft, stretch=1)
        self.hboxMain.addLayout(self.vboxRight, stretch=1)

    def closeEvent(self, event):
        event.accept()
        self.exitApp()

    def exitApp(self):
        self.timer.stop()
        if self.stepperController is not None:
            self.stepperController.disconnect()
        sys.exit()

    def setBotState(self):
        self.data.botActivated = self.activateBotCheckBox.checkState() == Qt.CheckState.Checked

    def getImageClickPos(self, event):
        x = event.pos().x()
        y = event.pos().y()
        if event.button() == 2:
            moveX, moveY = x, y
            moveX = TABLE_MAX_X - moveX
            self.logTextbox.append(f"Clicked on {x},{y} in image, moving to {int(moveX)},{int(moveY)}.")
            self.sendMoveValues(moveX, moveY)

    def sendMoveValues(self, x, y, type=MoveType.IMMEDIATE, label=None):
        if isinstance(type, MoveType):
            move_type = type
        elif isinstance(type, str):
            move_type = MoveType.IMMEDIATE
            label = type
        else:
            move_type = MoveType.IMMEDIATE
        if label is None:
            label = "Unknown"
        self.logTextbox.append(f"Move To: X={x:.0f}, Y={y:.0f}, \t\tMove Label: {label}, \t\tMove Type: {move_type.name}")
        self.data.lastMovePosition = (x, y)
        self.data.positionsSent += 1
        if self.stepperController is not None:
            #self.stepperController.cancel_jog()
            self.stepperController.wait_for_idle()
            self.stepperController.move_to_position(x, y)

    def calibrate(self):
        if self.stepperController is not None:
            self.logTextbox.append("Calibrating and moving home...")
            self.stepperController.calibrate()
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
                x = self.xCoordTextBox.value()
                y = self.yCoordTextBox.value()
                self.logTextbox.append("Moving to X=" + str(x) + ", Y=" + str(y))
                self.sendMoveValues(x, y, MoveType.IMMEDIATE, "UI Manual Move")
            except ValueError:
                self.logTextbox.append("ERROR: X and/or Y value is not an integer.")
        else:
            self.logTextbox.append("ERROR: Cannot move to position. No Arduino found on " + STEPPER_COM_PORT + ".")

    def updatePreCalculationUi(self, x, y, robotX, robotY):
        self.puckXLabel.setText(f"X: {x:.0f}")
        self.puckYLabel.setText(f"Y: {y:.0f}")
        self.puckSpeedLabel.setText(f"Speed: {self.data.puckSpeed:.1f}")
        self.robotXLabel.setText(f"X: {robotX:.0f}")
        self.robotYLabel.setText(f"Y: {robotY:.0f}")

    def updatePostCalculationUi(self, frame):
        def draw_arrow(img, pt1, pt2, color):
            cv2.arrowedLine(img, pt1, pt2, (0, 0, 0), thickness=5, tipLength=0.03)
            cv2.arrowedLine(img, pt1, pt2, color, thickness=2, tipLength=0.03)

        cv2.circle(frame, (int(self.data.savedPoint[0]), int(self.data.savedPoint[1])), 6, (255, 255, 255), -1)
        cv2.circle(frame, (int(self.data.savedPoint[0]), int(self.data.savedPoint[1])), 4, (0, 0, 0), -1)

        if self.data.predictionMade and self.data.predictionLine.get_m() is not None:
            if self.data.showDebugImages:
                cv2.circle(frame, (int(self.data.predictedPoint[0]), int(self.data.predictedPoint[1])), 6, (0, 0, 0), -1)
                cv2.circle(frame, (int(self.data.predictedPoint[0]), int(self.data.predictedPoint[1])), 4, (255, 0, 255), -1)

                if not self.data.puckCollides:
                    draw_arrow(
                        frame,
                        (int(self.data.currentPosition[0]), int(self.data.currentPosition[1])),
                        (int(self.data.predictedPoint[0]), int(self.data.predictedPoint[1])),
                        (0, 200, 255),
                    )

            if self.data.puckCollides and len(self.data.collisionPoints) > 0:
                draw_arrow(
                    frame,
                    (int(self.data.savedPoints[0][0]), int(self.data.savedPoints[0][1])),
                    (int(self.data.collisionPoints[0][0]), int(self.data.collisionPoints[0][1])),
                    (0, 150, 255),
                )
                for i in range(len(self.data.predictedPoints)):
                    cv2.circle(frame, (int(self.data.collisionPoints[i][0]), int(self.data.collisionPoints[i][1])), 8, (0, 0, 0), -1)
                    cv2.circle(frame, (int(self.data.collisionPoints[i][0]), int(self.data.collisionPoints[i][1])), 5, (255, 255, 255), -1)
                    draw_arrow(
                        frame,
                        (int(self.data.collisionPoints[i][0]), int(self.data.collisionPoints[i][1])),
                        (int(self.data.predictedPoints[i][0]), int(self.data.predictedPoints[i][1])),
                        (0, 255, 255),
                    )

        if self.data.showDebugImages:
            self.updateImageFromFrame(self.cameraImageLabel, frame)

    def updateImageFromFrame(self, image, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, ch = frame.shape
        bytesPerLine = ch * width
        qtImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        image.setPixmap(QPixmap(qtImg))

    def updateFrameTime(self):
        try:
            delta = (self.data.currentFrameTimestamp - self.data.lastFrameTimestamp).total_seconds()
            frameTimeMs = delta * 1000
            self.data.frameTimes.append(frameTimeMs)
            average = sum(self.data.frameTimes) / len(self.data.frameTimes)
            fps = 1000 / average if average > 0 else 0
            self.frameTimeLabel.setText(f"Frame Time: {average:.2f}ms ({fps:.0f} FPS)")
        except Exception:
            pass

    def preUpdate(self):
        if not self.cameraReceiver.new_data:
            return

        cam_data = self.cameraReceiver.get_latest()
        x = float(cam_data["puck_x"])
        y = float(cam_data["puck_y"])
        robot_x = float(cam_data["robot_x"])
        robot_y = float(cam_data["robot_y"])
        self.data.currentFrameTimestamp = cam_data.get("timestamp") or datetime.now()

        self.updatePreCalculationUi(x, y, robot_x, robot_y)

        self.controller.update({
            "x": x,
            "y": y,
            "robotX": robot_x,
            "robotY": robot_y,
        })

        frame = np.zeros((CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT, 3), dtype=np.uint8)

        if self.controller.debugTargetCam is not None:
            debugX, debugY = self.controller.debugTargetCam
            debugX = max(20, min(CAMERA_FRAME_HEIGHT - 20, int(debugX)))
            debugY = max(20, min(CAMERA_FRAME_WIDTH - 20, int(debugY)))
            cv2.circle(frame, (debugX, debugY), 22, (255, 0, 255), 4)

        self.updatePostCalculationUi(frame)
        self.updateFrameTime()


if __name__ == "__main__":
    cv2.ocl.setUseOpenCL(True)
    app = QApplication(sys.argv)
    splash = QSplashScreen(QPixmap("splash.png"))
    splash.show()
    main_window = MainWindow()
    splash.close()

    stream = QFile("style.qss")
    stream.open(QIODevice.ReadOnly)
    main_window.setStyleSheet(QTextStream(stream).readAll())

    font = QFont("Courier New")
    app.setFont(font)

    main_window.show()
    sys.exit(app.exec_())
