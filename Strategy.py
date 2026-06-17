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

    def update(self, calcData: dict = None):
        if not calcData:
            return

        x, y, self.data.robotX, self.data.robotY = (
            calcData["x"],
            calcData["y"],
            calcData["robotX"],
            calcData["robotY"],
        )

        self.data.puckPosition = (x, y)
        self.data.robotPosition = (self.data.robotX, self.data.robotY)

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
            int(self.data.puckPosition[0]),
            int(self.data.puckPosition[1]),
        )

        if self.state == State.DEFENDING:
            if (
                self.data.puckPosition[0] < STATE_PLAYBACK_X_THRESHOLD
                and self._speed() < STATE_TRANSITION_SPEED_THRESHOLD
            ):
                self.state = State.PLAYING_BACK

            self.defend()

        elif self.state == State.PLAYING_BACK:
            if (
                self.data.puckPosition[0] > STATE_PLAYBACK_X_THRESHOLD
                or self._speed() > STATE_TRANSITION_SPEED_THRESHOLD
            ):
                self.state = State.DEFENDING
            self.playBack()

        self._saveState()

    def _calculateVelocity(self):
        # Calculate time delta in seconds
        time_delta = (self.data.currentFrameTimestamp - self.data.lastFrameTimestamp).total_seconds()
        
        # Avoid division by zero
        if time_delta <= 0:
            self.data.velocity = (0, 0)
            return
        
        # Calculate position change
        dx = self.data.puckPosition[0] - self.data.lastPosition[0]
        dy = self.data.puckPosition[1] - self.data.lastPosition[1]
        
        # Calculate velocity as distance per second
        self.data.velocity = (dx / time_delta, dy / time_delta)


    def _resetPrediction(self):
        self.data.predictionMade = False
        self.data.predictedPoint = None
        self.data.savedPoints = []
        self.data.predictedPoints = []
        self.data.collisionPoints = []

    def _speed(self):
        return np.linalg.norm(self.data.velocity)

    def _collision_point_from_line(self, line):
        if line.get_angle() >= 0:
            wall_x = 0 + (PUCK_RADIUS / 2)
        else:
            wall_x = CAMERA_FRAME_HEIGHT - (PUCK_RADIUS / 2)

        wall_y = line.get_y(wall_x)
        if wall_y is None:
            return None

        return (wall_x, wall_y)

    def _build_reflection_line(self, collision_point, source_line, speed):
        multiplier = (
            REFLECTION_FAST_MULTIPLIER
            if speed > REFLECTION_FAST_SPEED_THRESHOLD
            else REFLECTION_NORMAL_MULTIPLIER
        )
        return Line(collision_point, None, (-1 * source_line.get_m() * multiplier))

    def _defensive_target_from_line(self, line, speed):
        attack_y = DEFENSIVE_LINE + GOFORWARD_MAX
        attack_x = line.get_x(attack_y)

        if GOLEFT_MAX < attack_x < GORIGHT_MAX and speed < ATTACK_LANE_SPEED_MAX:
            return (attack_x, attack_y)

        return (line.get_x(ROBOT_DEFEND_Y), ROBOT_DEFEND_Y)

    def _set_prediction(self, predicted_point):
        self.data.predictedPoint = predicted_point
        self.data.predictionMade = True
        self.data.wentBackToGoal = False
        self.data.attacked = False

    def _makePrediction(self):
        self.data.puckCollides = False
        self.data.lastCollisionPoint = self.data.puckPosition
        self.data.savedPoints = []
        self.data.predictedPoints = []
        self.data.collisionPoints = []

        speed = self._speed()
        self.data.predictionLine = Line(self.data.lastPosition, self.data.puckPosition)
        self.data.savedPoint = self.data.puckPosition

        try:
            if speed <= PREDICTION_MIN_SPEED or self.data.predictionLine.get_m() is None:
                return False

            current_line = self.data.predictionLine
            for _ in range(PREDICTION_MAX_BOUNCES):
                collision_point = self._collision_point_from_line(current_line)
                if collision_point is None:
                    break

                self.data.collisionPoint = collision_point
                self.data.lastCollisionPoint = collision_point
                self.data.puckCollides = True
                self.data.savedPoints.append(self.data.savedPoint)
                self.data.collisionPoints.append(collision_point)

                if collision_point[1] <= 0:
                    predicted_point = self._defensive_target_from_line(current_line, speed)
                    self._set_prediction(predicted_point)
                    break

                self.data.reflectionLine = self._build_reflection_line(
                    collision_point, current_line, speed
                )
                predicted_point = (
                    self.data.reflectionLine.get_x(ROBOT_DEFEND_Y),
                    ROBOT_DEFEND_Y,
                )
                self._set_prediction(predicted_point)
                self.data.predictedPoints.append(predicted_point)

                current_line = self.data.reflectionLine
                self.data.predictionLine = current_line

            return self.data.predictionMade
        except Exception as e:
            print("Prediction error:", e)
            return False

    def _get_target_from_prediction(self):
        target_x, target_y = self.data.puckPosition
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

        # At very high puck speed, prediction can be noisy. Track the current puck Y
        # on the defensive line instead of doing nothing.
        if self._speed() > SPEED_THRESHOLD:
            fastTargetY = max(0, min(self.data.puckPosition[1], TABLE_MAX_Y))
            self.debugTargetCam = (int(DEFENSIVE_LINE), int(fastTargetY))
            self.moveIfPossible(DEFENSIVE_LINE, fastTargetY, "Defense Fast")
            return

        self.moveIfPossible(DEFENSIVE_LINE, targetY, "Defense")

    def _goHome(self):
        self.lastPlaybackMove = None
        if self.data.botActivated:
            self.moveIfPossible(ROBOT_HOME_X_CAM, ROBOT_HOME_Y, "Homing")

    def playBack(self):
        if not self.data.botActivated:
            return

        moveX, moveY = self.data.puckPosition[0], self.data.puckPosition[1]

        self.moveIfPossible(moveX, moveY, "Play Back")

    def _saveState(self):
        self.data.wasPuckGoingToRobot = self.data.velocity[0] < 0
        self.data.lastPosition = self.data.puckPosition
        self.data.lastFrameTimestamp = self.data.currentFrameTimestamp

    def isPuckBehindRobot(self):
        if self.data.robotPosition[1] == -1:
            return False

        if self.data.puckPosition[0] < 0 or self.data.puckPosition[1] < 0:
            return False

        return self.data.robotPosition[1] > self.data.puckPosition[1] and self.data.puckPosition[0] - CAMERA_FRAME_WIDTH/6 < self.data.robotPosition[0] < self.data.puckPosition[0] + CAMERA_FRAME_WIDTH/6

    def moveIfPossible(self, x, y, move_label):
        if self.isPuckBehindRobot():
            return

        self.sendMoveValues(int(x), int(y), move_label)