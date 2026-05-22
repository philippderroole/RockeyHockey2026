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
        self.atHome = True
        self.debugTargetCam = None
        self.debugStartLocked = False
        self.debugInitialized = False
        self.lastPlaybackMove = None
        self.playbackDeadzone = 120


    def update(self, calcData: dict = None):
        start_time = time.time()
        if calcData:
            
            x, y, radius, self.data.robotX, self.data.robotY, self.data.robotRadius, frame = (
                calcData["x"],
                calcData["y"],
                calcData["radius"],
                calcData["robotX"],
                calcData["robotY"],
                calcData["robotRadius"],
                calcData["frame"]
            )

        if self.data.robotRadius < 10 or self.data.robotRadius > 50:
            self.data.robotX, self.data.robotY, self.data.robotRadius = -1, -1, -1

        #print(f"STATE: {self.state}")
        self.data.currentPosition = (x, y)

        frame = self.updatePreCalculationUi(
            frame, x, y, radius, self.data.robotX, self.data.robotY, self.data.robotRadius
        )
        if x < 0 or y < 0:
            return frame

        self.data.puckSpeed = self._calculateSpeed()
        self._resetPrediction()
        self._makePrediction(radius)
        self.isPuckGoingToRobot = self._isGoingToRobot()
        print("STATE:", self.state, "isGoing:", self.isPuckGoingToRobot)
        print("isPuckGoingToRobot:", self.isPuckGoingToRobot)

        if self.state == State.IDLE:
            self.debugTargetCam = (int(ROBOT_HOME_X_CAM), int(ROBOT_HOME_Y))

            if self.isPuckGoingToRobot:
                self.state = State.DEFENDING
                self._moveToPredicted()

        elif self.state == State.DEFENDING:
            self._moveToPredicted()

            if not self.isPuckGoingToRobot:
                self.state = State.HOMING

        elif self.state == State.HOMING:
            self.debugTargetCam = (int(ROBOT_HOME_X_CAM), int(ROBOT_HOME_Y))
            self._goHome()

            if self._atHome():
                self.state = State.IDLE

        elif self.state == State.PLAYING_BACK:
            self.debugTargetCam = (
                int(self.data.currentPosition[0]),
                int(self.data.currentPosition[1])
            )
            self._playBack()

            if self._playedBack():
                self.state = State.HOMING

        self._saveState()
        end_time = time.time()
        zeit = end_time - start_time
        #print(f"Benötigte Zeit: {zeit}")
        return frame

    def _calculateSpeed(self):
        dx = self.data.currentPosition[0] - self.data.lastPosition[0]
        dy = self.data.currentPosition[1] - self.data.lastPosition[1]

        try:
            delta = self.data.currentFrameTimestamp - self.data.lastFrameTimestamp

            # Falls datetime → convert
            if hasattr(delta, "total_seconds"):
                delta = delta.total_seconds()

        except Exception:
            delta = 0

        if delta != 0:
            return math.sqrt(dx ** 2 + dy ** 2) / abs(delta)

        return math.sqrt(dx ** 2 + dy ** 2)
        
        

    def _isGoingToRobot(self):
        return (
            self.data.currentPosition[1] < self.data.lastPosition[1]
            and abs(self.data.currentPosition[1] - self.data.lastPosition[1]) > 2
        )

    def _isAbleToAttack(self):
        # logik falls puck sich im Bereich des Roboters befindet und sich so bewegt, dass Roboter angreifen kann
        # check if Puck is staying in own half
        return False

    def _resetPrediction(self):
        self.data.predictionMade = False
        self.data.savedPoints = []
        self.data.predictedPoints = []
        self.data.collisionPoints = []

    def _makePrediction(self, radius):
        # Vorhersagelogik (gekürzt/eingekapselt)
        # Setze self.predictedPoint etc.
        # check if new prediciton is needed (because reflection has taken place)
        #print(f"if ({len(self.data.predictedPoints) >= 1 and self.data.lastPosition[1] < self.data.collisionPoints[0][1]}) setze predictionMade = False")
        if (
            len(self.data.predictedPoints) >= 1
            and self.data.lastPosition[1] < self.data.collisionPoints[0][1]
        ):
            self.data.predictionMade = False
        #print(f"predictionMade: {self.data.predictionMade}")
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
                #print(f"das muss true sein: {self.data.predictionLine.get_m() is not None and self.data.currentPosition[1] < 550 and self.data.puckSpeed > 4}")
                #print(self.data.predictionLine.get_m())
                #print(self.data.currentPosition[1])
                #print(self.data.puckSpeed)
                if self.data.puckSpeed > 1.5 and self.data.predictionLine.get_m() is not None:
                    # time.sleep(3)
                    loopCounter = 0
                    while loopCounter < 2:
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
                                #print(
                                    #f"Reflection line speed > 28 m={self.data.reflectionLine.get_m()}"
                                #)
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
                                #print(
                                   #f"Reflection line m={self.data.reflectionLine.get_m()}"
                                #)
                            self.data.predictedPoint = (
                                self.data.reflectionLine.get_x(ROBOT_DEFEND_Y),
                                ROBOT_DEFEND_Y,
                            )
                            self.data.predictionMade = True
                            #print(f"{self.data.currentPosition[1]} warum?")
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
                                        ROBOT_DEFEND_Y
                                    ),
                                    ROBOT_DEFEND_Y,
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

            except Exception as e:
                print("Prediction error:", e)
                pass
        return True 


    def _moveToPredicted(self):
        targetX = self.data.currentPosition[0]
        targetY = self.data.currentPosition[1]

        if hasattr(self.data, "predictedPoint") and self.data.predictedPoint:
            if self.data.predictedPoint[0] is not None and self.data.predictedPoint[1] is not None:
                targetX = self.data.predictedPoint[0]
                targetY = self.data.predictedPoint[1]

        targetX = max(40, min(CAMERA_FRAME_HEIGHT - 40, targetX))
        targetY = max(ROBOT_HOME_Y - 10, min(ROBOT_HOME_Y + 140, targetY))

        self.debugTargetCam = (int(targetX), int(targetY))

        if not self.data.botActivated:
            return
        
        # Geschwindigkeitsfilter: Verhindert unnötige Befehle bei Tracking-Fehlern
        if self.data.puckSpeed > 20:
            return

        moveX, moveY = self.mapCoordinates(
            targetX,
            targetY,
            CAMERA_FRAME_HEIGHT,
            CAMERA_FRAME_ROBOT_MAX_Y,
            TABLE_MAX_X,
            TABLE_MAX_Y,
        )
        moveX = TABLE_MAX_X - moveX
        self.moveIfPossible(moveX, moveY, "Defense")

    def _goHome(self):
        self.lastPlaybackMove = None
        if self.data.botActivated:
            moveX, moveY = self.mapCoordinates(
                ROBOT_HOME_X_CAM,
                ROBOT_HOME_Y,
                CAMERA_FRAME_HEIGHT,
                CAMERA_FRAME_ROBOT_MAX_Y,
                TABLE_MAX_X,
                TABLE_MAX_Y,
            )
            moveX = TABLE_MAX_X - moveX

            self.moveIfPossible(moveX, moveY, "Homing")
            self.atHome = True

    def _playBack(self):
        # Playback-Logik bei langsamem Puck in eigenem Feld
        if not self.data.botActivated:
            return

        offsetX = 0
        if self.data.currentPosition[0] < 120:
            offsetX = -20
        if self.data.currentPosition[0] > 280:
            offsetX = 20

        moveX, moveY = self.mapCoordinates(
            self.data.currentPosition[0] + offsetX,
            self.data.currentPosition[1] + 10,
            CAMERA_FRAME_HEIGHT,
            CAMERA_FRAME_ROBOT_MAX_Y,
            TABLE_MAX_X,
            TABLE_MAX_Y,
        )
        moveX = TABLE_MAX_X - moveX

        if self.lastPlaybackMove is not None:
            lastX, lastY = self.lastPlaybackMove
            if abs(moveX - lastX) < self.playbackDeadzone and abs(moveY - lastY) < self.playbackDeadzone:
                return

        self.moveIfPossible(moveX, moveY, "Play Back")
        self.lastPlaybackMove = (moveX, moveY)
        self.data.attackedPoint = self.data.currentPosition
        # Nur ausgeben wenn Puck sich in Richtung Roboter bewegt
        if self.data.currentPosition[1] < self.data.lastPosition[1]:
            print(f"Attacking: {self.data.currentPosition[0]}, {self.data.currentPosition[1]}")


    def _playedBack(self):
        # Logik zur erkennung ob Puck zurückgespielt wurde
        # Fallback einbauen, falls Roboter Puck nicht getroffen hat
        # dieser soll dann zurück in PREDICTION FALLEN
        is_near = abs(self.data.attackedPoint[0] - self.data.robotX) < 40 and abs(self.data.attackedPoint[1] - self.data.robotY) < 40
        return is_near

    def _atHome(self):
        if abs(ROBOT_HOME_X_CAM - self.data.robotX) > 40 or abs(ROBOT_HOME_Y - self.data.robotY) > 40:
            return False
        return True

    def _saveState(self):
        self.data.wasPuckGoingToRobot = self.isPuckGoingToRobot
        self.data.lastPosition = self.data.currentPosition
        self.data.lastFrameTimestamp = self.data.currentFrameTimestamp

    def mapCoordinates(
        self, x, y, maxWidthFrom, maxHeightFrom, maxWidthTo, maxHeightTo
    ):
        # Scale so it fits the other coordinate system
        xScale = maxWidthTo / maxWidthFrom
        yScale = maxHeightTo / maxHeightFrom
        x = x * xScale
        y = y * yScale
        return x, y
    
    def isPuckBehindRobot(self):
        # Robot was not detected
        if self.data.robotY == -1:
            return False

        return self.data.robotY > self.data.currentPosition[1] and self.data.currentPosition[0] - CAMERA_FRAME_WIDTH/6 < self.data.robotX < self.data.currentPosition[0] + CAMERA_FRAME_WIDTH/6

    def moveIfPossible(self, x, y, type):
        if self.isPuckBehindRobot():
            return
        self.sendMoveValues(int(x), int(y), type)


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