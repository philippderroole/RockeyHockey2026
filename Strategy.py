from DataModel import model
from Camera import Camera
from Constants import *
from datetime import datetime
import numpy as np
import cv2
import math
import time
from Processing.Line import Line
from Processing.ProcessFrame import processFrame


class State:
    IDLE = "IDLE"
    TRACKING = "TRACKING"
    PREDICTING = "PREDICTING"
    DEFENDING = "DEFENDING"
    HOMING = "HOMING"
    PLAYING_BACK = "PLAYING_BACK"


class RobotController:
    def __init__(self, sendMoveValues, updatePreCalculationUi, camera):
        self.data = model
        self.state = State.IDLE
        self.sendMoveValues = sendMoveValues
        self.updatePreCalculationUi = updatePreCalculationUi
        self.camera = camera


    def update(self, calcData: dict = None):
        start_time = time.time()
        if calcData:
            global radius
            x, y, radius, robotX, robotY, robotRadius, frame = (
                calcData["x"],
                calcData["y"],
                calcData["radius"],
                calcData["robotX"],
                calcData["robotY"],
                calcData["robotRadius"],
                calcData["frame"]
            )

        if robotRadius < 10 or robotRadius > 50:
            robotX, robotY, robotRadius = -1, -1, -1

        print(f"STATE: {self.state}")
        self.data.currentPosition = (x, y)

        self.data.puckSpeed = self._calculateSpeed()
        frame = self.updatePreCalculationUi(
            frame, x, y, radius, robotX, robotY, robotRadius
        )
        self.isPuckGoingToRobot = self._isGoingToRobot()
        self._resetPrediction()
        self._makePrediction(frame)

        if self.state == State.IDLE:
            if self.isPuckGoingToRobot:
                print("Changed State from IDLE to PREDICTING")
                self.state = State.PREDICTING
            elif self._isAbleToAttack():
                print("Changed State from IDLE to PLAYING_BACK")
                self.state = State.PLAYING_BACK

        elif self.state == State.DEFENDING:
            self._moveToPredicted()
            if not self.isPuckGoingToRobot:
                print("Changed State from DEFENDING to HOMING")
                self.state = State.HOMING

        elif self.state == State.HOMING:
            self._goHome()
            if self._atHome():
                print("Changed State from HOMING to IDLE")
                self.state = State.IDLE

        elif self.state == State.PLAYING_BACK:
            self._playBack()
            if self._playedBack():
                print("Changed State from PLAYING_BACK to HOMING")
                self.state = State.HOMING

        self._saveState()
        end_time = time.time()
        zeit = end_time - start_time
        print(f"Benötigte Zeit: {zeit}")
        return frame

    def _calculateSpeed(self):
        dx = self.data.currentPosition[0] - self.data.lastPosition[0]
        dy = self.data.currentPosition[1] - self.data.lastPosition[1]
        return math.sqrt(dx ** 2 + dy ** 2)

    def _isGoingToRobot(self):
        return self.data.currentPosition[1] < self.data.lastPosition[1] and abs(self.data.lastPosition[1] - self.data.currentPosition[1]) > 1

    def _isAbleToAttack(self):
        # logik falls puck sich im Bereich des Roboters befindet und sich so bewegt, dass Roboter angreifen kann
        # check if Puck is staying in own half
        return self.data.puckSpeed < 3 and GOLEFT_MAX < self.data.currentPosition[0] < GORIGHT_MAX and self.data.currentPosition[1] < GOFORWARD_MAX

    def _resetPrediction(self):
        self.data.predictionMade = False
        self.data.savedPoints = []
        self.data.predictedPoints = []
        self.data.collisionPoints = []

    def _makePrediction(self, frame):
        # Vorhersagelogik (gekürzt/eingekapselt)
        # Setze self.predictedPoint etc.
        # check if new prediciton is needed (because reflection has taken place)
        print(f"if ({len(self.data.predictedPoints) >= 1 and self.data.lastPosition[1] < self.data.collisionPoints[0][1]}) setze predictionMade = False")
        if (
            len(self.data.predictedPoints) >= 1
            and self.data.lastPosition[1] < self.data.collisionPoints[0][1]
        ):
            self.data.predictionMade = False
        print(f"predictionMade: {self.data.predictionMade}")
        if not self.data.predictionMade:
            self.data.puckCollides = False

            # das passt sicher nicht  :)
            if len(self.data.collisionPoints) >= 1:
                self.data.lastCollisionPoint = self.data.collisionPoints[0]
            else:
                self.data.lastCollisionPoint = self.data.currentPosition
            # reset saved points
            self.data.savedPoints = []
            self.data.predictedPoints = []
            self.data.collisionPoints = []

            # Draw line between current and last puck position
            self.data.predictionLine = Line(
                self.data.lastPosition, self.data.currentPosition
            )

            self.data.savedPoint = self.data.currentPosition

            try:
                print(f"das muss true sein: {self.data.predictionLine.get_m() is not None and self.data.currentPosition[1] < 550 and self.data.puckSpeed > 4}")
                print(self.data.predictionLine.get_m())
                print(self.data.currentPosition[1])
                print(self.data.puckSpeed)
                if self.data.puckSpeed > 4 and self.data.predictionLine.get_m():
                    # time.sleep(3)
                    loopCounter = 0
                    while loopCounter < 5:
                        # Check if puck collides with a wall
                        if (
                            self.data.predictionLine.get_angle() >= 0
                        ):  # left edge
                            self.data.collisionPoint = (
                                0 + (radius / 2),
                                self.data.predictionLine.get_y(0 + (radius / 2)),
                            )
                            self.data.puckCollides = True
                        else:  # right edge
                            self.data.collisionPoint = (
                                CAMERA_FRAME_HEIGHT - (radius / 2),
                                self.data.predictionLine.get_y(
                                    CAMERA_FRAME_HEIGHT - (radius / 2)
                                ),
                            )
                            self.data.puckCollides = True

                        # save things for UI #1
                        self.data.savedPoints.append(self.data.savedPoint)
                        self.data.collisionPoints.append(self.data.collisionPoint)
                        

                        # If puck collides with wall calculate the reflection point
                        if self.data.puckCollides and self.data.collisionPoint[1] > 0:
                            #time.sleep(3)
                            if self.data.puckSpeed > 28:
                                self.data.reflectionLine = Line(
                                    self.data.collisionPoint,
                                    None,
                                    (
                                        -1
                                        * self.data.predictionLine.get_m()
                                        * 2.5
                                    ),
                                )
                                print(
                                    f"Reflection line speed > 28 m={self.data.reflectionLine.get_m()}"
                                )
                            else:
                                self.data.reflectionLine = Line(
                                    self.data.collisionPoint,
                                    None,
                                    (
                                        -1
                                        * self.data.predictionLine.get_m()
                                        * 1.7
                                    ),  # original value 2.5
                                )
                                print(
                                    f"Reflection line m={self.data.reflectionLine.get_m()}"
                                )
                            self.data.predictedPoint = (
                                self.data.reflectionLine.get_x(DEFENSIVE_LINE),
                                DEFENSIVE_LINE,
                            )
                            self.data.predictionMade = True
                            print(f"{self.data.currentPosition[1]} warum?")
                            self.data.wentBackToGoal = False
                            self.data.attacked = False
                        else:
                            # check if puck is arriving in specific area
                            if (
                                GOLEFT_MAX
                                < self.data.predictionLine.get_x(
                                    DEFENSIVE_LINE + GOFORWARD_MAX
                                )
                                < GORIGHT_MAX
                                and self.data.puckSpeed < 15
                            ):
                                self.data.predictedPoint = (
                                    self.data.predictionLine.get_x(
                                        DEFENSIVE_LINE + GOFORWARD_MAX
                                    ),
                                    DEFENSIVE_LINE + GOFORWARD_MAX,
                                )
                            else:
                                self.data.predictedPoint = (
                                    self.data.predictionLine.get_x(
                                        DEFENSIVE_LINE
                                    ),
                                    DEFENSIVE_LINE,
                                )
                            self.data.predictionMade = True
                            self.data.wentBackToGoal = False
                            self.data.attacked = False
                            break
                        # save thigns for ui #2 reflection only
                        self.data.predictedPoints.append(self.data.predictedPoint)

                        self.data.predictionLine = self.data.reflectionLine
                        self.data.savedPoint = self.data.currentPosition
                        # frame = self.updatePostCalculationUi(frame)
                        loopCounter += 1

                    # Check if predicted puck position is valid
                    if GOLEFT_MAX < self.data.predictedPoint[0] < (GORIGHT_MAX):
                        # Calculate robot movement to the predicted puck position

                        moveX, moveY = self.mapCoordinates(
                            self.data.predictedPoint[0],
                            self.data.predictedPoint[1],
                            CAMERA_FRAME_HEIGHT,
                            CAMERA_FRAME_ROBOT_MAX_Y,
                            TABLE_MAX_X,
                            TABLE_MAX_Y,
                        )
                        moveX = TABLE_MAX_X - moveX

                        # If bot is activated move to the calculated position
                        if self.data.botActivated:
                            #self.logTextbox.append(f"{self.puckSpeed}")
                            self.data.positionsSent += 1
                            self.sendMoveValues(
                                int(moveX),
                                int(moveY),
                                "Defense/Active Defense",
                            )
            except Exception as e:
                print("in Exception, kp warum")
                print(e)
                time.sleep(10)
                pass
        return True 


    def _moveToPredicted(self):
        if self.data.predictionMade and self.data.botActivated:
            moveX, moveY = self.mapCoordinates(
                self.data.predictedPoint[0],
                self.data.predictedPoint[1],
                CAMERA_FRAME_HEIGHT,
                CAMERA_FRAME_ROBOT_MAX_Y,
                TABLE_MAX_X,
                TABLE_MAX_Y,
            )
            moveX = TABLE_MAX_X - moveX
            self.sendMoveValues(int(moveX), int(moveY), "Defense")

    def _goHome(self):
        moveX, moveY = self.mapCoordinates(
            (CAMERA_FRAME_HEIGHT / 2),
            DEFENSIVE_LINE,
            CAMERA_FRAME_HEIGHT,
            CAMERA_FRAME_ROBOT_MAX_Y,
            TABLE_MAX_X,
            TABLE_MAX_Y,
        )
        if self.data.botActivated:
            self.sendMoveValues(int(moveX), int(moveY), "Homing")

    def _playBack(self):
        # Playback-Logik bei langsamem Puck in eigenem Feld
        pass

    def _playedBack(self):
        # Logik zur erkennung ob Puck zurückgespielt wurde
        # Fallback einbauen, falls Roboter Puck nicht getroffen hat
        # dieser soll dann zurück in PREDICTION FALLEN
        return True

    def _atHome(self):
        # Prüfen, ob Roboter am Ziel ist
        return True

    def _saveState(self):
        self.data.wasPuckGoingToRobot = self.data.isPuckGoingToRobot
        self.data.lastPosition = self.data.currentPosition

    def mapCoordinates(
        self, x, y, maxWidthFrom, maxHeightFrom, maxWidthTo, maxHeightTo
    ):
        # Scale so it fits the other coordinate system
        xScale = maxWidthTo / maxWidthFrom
        yScale = maxHeightTo / maxHeightFrom
        x = x * xScale
        y = y * yScale
        return x, y
    
    
    


"""# schauen ob das so compiliert
def a():
    return True

def b():
    return True

# zum testen
controller = RobotController(a, b)
print(controller.state)
print(controller.data.targetPoint)
"""
