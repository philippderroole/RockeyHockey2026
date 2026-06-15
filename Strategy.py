from DataModel import model
from Constants import *
import numpy as np
from Processing.Line import Line


class State:
    DEFENDING = "DEFENDING"
    PLAYING_BACK = "PLAYING_BACK"

class RobotController:
    def __init__(self, sendMoveValues):
        self.data = model
        self.state = State.DEFENDING
        self.sendMoveValues = sendMoveValues
        self.debugTargetCam = None
        self.lastPlaybackMove = None
        self.playbackDeadzone = 120

    def update(self, calcData: dict = None):
        print("Current State:", self.state)
        print("velocity:", self.data.velocity)
        print(self.data.predictedPoint)
        print(self.data.predictedPoints)

        if not calcData:
            return

        x, y, self.data.robotX, self.data.robotY = (
            calcData["x"],
            calcData["y"],
            calcData["robotX"],
            calcData["robotY"],
        )

        self.data.currentPosition = (x, y)

        if x < 0 or y < 0:
            self._resetPrediction()

            self.state = State.DEFENDING
            self._goHome()
            self._saveState()
            return

        self._calculateVelocity()
        self._resetPrediction()
        self._makePrediction()

        self.debugTargetCam = (
            int(self.data.currentPosition[0]),
            int(self.data.currentPosition[1]),
        )

        if self.state == State.DEFENDING:
            if self.data.currentPosition[0] < 350 and np.linalg.norm(self.data.velocity) < 0.5:
                self.state = State.PLAYING_BACK

            self.defend()

        elif self.state == State.PLAYING_BACK:
            if self.data.currentPosition[0] > 350 or np.linalg.norm(self.data.velocity) > 0.5:
                self.state = State.DEFENDING
            self._playBack()

        self._saveState()

    def _calculateVelocity(self):
        self.data.velocity = (self.data.currentPosition[0] - self.data.lastPosition[0], self.data.currentPosition[1] - self.data.lastPosition[1])


    def _resetPrediction(self):
        self.data.predictionMade = False
        self.data.predictedPoint = None
        self.data.savedPoints = []
        self.data.predictedPoints = []
        self.data.collisionPoints = []

    def _makePrediction(self):
        if (
            len(self.data.predictedPoints) >= 1
            and self.data.lastPosition[1] < self.data.collisionPoints[0][1]
        ):
            self.data.predictionMade = False

        if not self.data.predictionMade:
            self.data.puckCollides = False

            if len(self.data.collisionPoints) >= 1:
                self.data.lastCollisionPoint = self.data.collisionPoints[0]
            else:
                self.data.lastCollisionPoint = self.data.currentPosition

            self.data.savedPoints = []
            self.data.predictedPoints = []
            self.data.collisionPoints = []

            self.data.predictionLine = Line(
                self.data.lastPosition, self.data.currentPosition
            )

            self.data.savedPoint = self.data.currentPosition

            try:
                if np.linalg.norm(self.data.velocity) > 0.5 and self.data.predictionLine.get_m() is not None:
                    loopCounter = 0
                    while loopCounter < 2:
                        if self.data.predictionLine.get_angle() >= 0:
                            self.data.collisionPoint = (
                                0 + (PUCK_RADIUS / 2),
                                self.data.predictionLine.get_y(0 + (PUCK_RADIUS / 2)),
                            )
                            self.data.puckCollides = True
                        else:
                            self.data.collisionPoint = (
                                CAMERA_FRAME_HEIGHT - (PUCK_RADIUS / 2),
                                self.data.predictionLine.get_y(
                                    CAMERA_FRAME_HEIGHT - (PUCK_RADIUS / 2)
                                ),
                            )
                            self.data.puckCollides = True

                        self.data.savedPoints.append(self.data.savedPoint)
                        self.data.collisionPoints.append(self.data.collisionPoint)

                        if self.data.puckCollides and self.data.collisionPoint[1] > 0:
                            if np.linalg.norm(self.data.velocity) > 28:
                                self.data.reflectionLine = Line(
                                    self.data.collisionPoint,
                                    None,
                                    (
                                        -1
                                        * self.data.predictionLine.get_m()
                                        * 2.5
                                    ),
                                )
                            else:
                                self.data.reflectionLine = Line(
                                    self.data.collisionPoint,
                                    None,
                                    (
                                        -1
                                        * self.data.predictionLine.get_m()
                                        * 1.7
                                    ),
                                )

                            self.data.predictedPoint = (
                                self.data.reflectionLine.get_x(ROBOT_DEFEND_Y),
                                ROBOT_DEFEND_Y,
                            )
                            self.data.predictionMade = True
                            self.data.wentBackToGoal = False
                            self.data.attacked = False
                        else:
                            if (
                                GOLEFT_MAX
                                < self.data.predictionLine.get_x(
                                    DEFENSIVE_LINE + GOFORWARD_MAX
                                )
                                < GORIGHT_MAX
                                and np.linalg.norm(self.data.velocity) < 15
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

                        self.data.predictedPoints.append(self.data.predictedPoint)

                        self.data.predictionLine = self.data.reflectionLine
                        self.data.savedPoint = self.data.currentPosition
                        loopCounter += 1

            except Exception as e:
                print("Prediction error:", e)

        return True

    def _get_target_from_prediction(self):
        target_x, target_y = self.data.currentPosition
        predicted = getattr(self.data, "predictedPoint", None)

        if self.data.predictionMade and predicted is not None:
            if predicted[0] is not None and predicted[1] is not None:
                target_x, target_y = predicted

        return target_x, target_y

    def defend(self):
        if not self.data.botActivated:
            return

        targetX, targetY = self._get_target_from_prediction()
        self.debugTargetCam = (int(targetX), int(targetY))

        if np.linalg.norm(self.data.velocity) > 20:
            return

        self.moveIfPossible(20, targetY, "Defense")

    def _goHome(self):
        self.lastPlaybackMove = None
        if self.data.botActivated:
            self.moveIfPossible(ROBOT_HOME_X_CAM, ROBOT_HOME_Y, "Homing")

    def _playBack(self):
        if not self.data.botActivated:
            return

        offsetX = 0
        if self.data.currentPosition[0] < 120:
            offsetX = -20
        if self.data.currentPosition[0] > 280:
            offsetX = 20

        moveX, moveY = self.data.currentPosition[0] + offsetX, self.data.currentPosition[1] + 10

        if self.lastPlaybackMove is not None:
            lastX, lastY = self.lastPlaybackMove
            if abs(moveX - lastX) < self.playbackDeadzone and abs(moveY - lastY) < self.playbackDeadzone:
                return

        self.moveIfPossible(moveX, moveY, "Play Back")
        self.lastPlaybackMove = (moveX, moveY)
        self.data.attackedPoint = self.data.currentPosition

        if self.data.currentPosition[1] < self.data.lastPosition[1]:
            print(f"Attacking: {self.data.currentPosition[0]}, {self.data.currentPosition[1]}")

    def _saveState(self):
        self.data.wasPuckGoingToRobot = self.data.velocity[0] < 0
        self.data.lastPosition = self.data.currentPosition
        self.data.lastFrameTimestamp = self.data.currentFrameTimestamp

    def isPuckBehindRobot(self):
        if self.data.robotY == -1:
            return False

        if self.data.currentPosition[0] < 0 or self.data.currentPosition[1] < 0:
            return False

        return self.data.robotY > self.data.currentPosition[1] and self.data.currentPosition[0] - CAMERA_FRAME_WIDTH/6 < self.data.robotX < self.data.currentPosition[0] + CAMERA_FRAME_WIDTH/6

    def moveIfPossible(self, x, y, type):
        if self.isPuckBehindRobot():
            return

        self.sendMoveValues(int(x), int(y), type)