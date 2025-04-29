from DataModel import model
from Camera import Camera
from Constants import *
from datetime import datetime
import numpy as np
import cv2
from Processing.ProcessFrame import processFrame
class State:
    IDLE = "IDLE"
    TRACKING = "TRACKING"
    PREDICTING = "PREDICTING"
    DEFENDING = "DEFENDING"
    HOMING = "HOMING"
    PLAYING_BACK = "PLAYING_BACK"


class RobotController:
    def __init__(self, sendMoveValues, camera):
        self.data = model
        self.state = State.IDLE
        self.sendMoveValues = sendMoveValues
        self.camera = camera


    def update(self):
        if self.camera.stopped:
            print("Warning: Kamera neustarten...")
            self.camera = Camera(
                CAMERA_INDEX,
                CAMERA_FRAME_WIDTH,
                CAMERA_FRAME_HEIGHT,
                CAMERA_FOCUS,
                CAMERA_BUFFERSIZE,
                CAMERA_FRAMERATE,
                CAMERA_STREAM_URL,
            ).start()

        if not self.camera.new_frame:
            return

        frame = self.initializeCamera()
        if frame is None:
            return

        x, y, radius, robotX, robotY, robotRadius = processFrame(frame, self)

        if robotRadius < 10 or robotRadius > 50:
            robotX, robotY, robotRadius = -1, -1, -1

        self.currentPosition = (x, y)
        self.puckSpeed = self._calculateSpeed()
        self.isPuckGoingToRobot = self._isGoingToRobot()

        if self.state == State.IDLE:
            if self.isPuckGoingToRobot:
                self.state = State.PREDICTING
            if self._isAbleToAttack:
                self.state = State.PLAYING_BACK

        elif self.state == State.PREDICTING:
            self._resetPrediction()
            if self._makePrediction(frame):
                self.state = State.DEFENDING
            else:
                self.state = State.HOMING

        elif self.state == State.DEFENDING:
            self._moveToPredicted()
            if not self.isPuckGoingToRobot:
                self.state = State.HOMING

        elif self.state == State.HOMING:
            self._goHome()
            if self._atHome():
                self.state = State.IDLE

        elif self.state == State.PLAYING_BACK:
            self._playBack()
            self.state = State.HOMING


        # speicher für ui 
        frame = self.updatePostCalculationUi(frame)
        self._saveState()

    def _calculateSpeed(self):
        dx = self.currentPosition[0] - self.lastPosition[0]
        dy = self.currentPosition[1] - self.lastPosition[1]
        return math.sqrt(dx ** 2 + dy ** 2)

    def _isGoingToRobot(self):
        return self.currentPosition[1] < self.lastPosition[1] and abs(self.lastPosition[1] - self.currentPosition[1]) > 1

    def _isAbleToAttack(self):
        # logik falls puck sich im Bereich des Roboters befindet und sich so bewegt, dass Roboter angreifen kann
        return True

    def _resetPrediction(self):
        self.predictionMade = False
        self.savedPoints = []
        self.predictedPoints = []
        self.collisionPoints = []

    def _makePrediction(self, frame):
        # Deine Vorhersagelogik (gekürzt/eingekapselt)
        # Setze self.predictedPoint etc.
        return True  # Wenn Vorhersage erfolgreich


    def _moveToPredicted(self):
        if self.predictionMade and self.botActivated:
            moveX, moveY = self.mapCoordinates(
                self.predictedPoint[0],
                self.predictedPoint[1],
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
        if self.botActivated:
            self.sendMoveValues(int(moveX), int(moveY), "Homing")

    def _playBack(self):
        # Playback-Logik bei langsamem Puck in eigenem Feld
        pass

    def _playedBack(self):
        # Logik zur erkennung ob Puck zurückgespielt wurde
        # Fallback einbauen, falls Roboter Puck nicht getroffen hat
        # dieser soll dann zurück in PREDICTION FALLEN
        return False

    def _atHome(self):
        # Prüfen, ob Roboter am Ziel ist
        return True

    def _saveState(self):
        self.wasPuckGoingToRobot = self.isPuckGoingToRobot
        self.lastPosition = self.currentPosition
    
    def updatePostCalculationUi(self, frame):
        if self.predictionMade and self.predictionLine.get_m() is not None:
            if self.showDebugImages:
                # Draw predicted and current puck position
                cv2.circle(
                    frame,
                    (int(self.predictedPoint[0]), int(self.predictedPoint[1])),
                    5,
                    (255, 0, 255),
                    -1,
                )
                cv2.circle(
                    frame,
                    (int(self.savedPoint[0]), int(self.savedPoint[1])),
                    5,
                    (0, 0, 0),
                    -1,
                )

                # Draw predicted line
                if not self.puckCollides:
                    cv2.line(
                        frame,
                        (int(self.currentPosition[0]), int(self.currentPosition[1])),
                        (int(self.predictedPoint[0]), int(self.predictedPoint[1])),
                        (255, 0, 0),
                        thickness=2,
                        lineType=4,
                    )
                    cv2.line(
                        frame,
                        (int(self.savedPoint[0]), int(self.savedPoint[1])),
                        (int(self.predictedPoint[0]), int(self.predictedPoint[1])),
                        (255, 0, 0),
                        thickness=2,
                        lineType=4,
                    )

            # Draw prediction line before collision
            cv2.line(
                frame,
                (int(self.savedPoints[0][0]), int(self.savedPoints[0][1])),
                (int(self.collisionPoints[0][0]), int(self.collisionPoints[0][1])),
                (255, 0, 0),
                thickness=2,
                lineType=4,
            )
            # Executed if the puck collides with a wall
            if self.puckCollides:
                if len(self.collisionPoints) > 0:
                    for i in range(len(self.predictedPoints)):
                        # Draw collision point
                        cv2.circle(
                            frame,
                            (
                                int(self.collisionPoints[i][0]),
                                int(self.collisionPoints[i][1]),
                            ),
                            10,
                            (255, 255, 255),
                            -1,
                        )
                        # Draw reflection line after collision
                        cv2.line(
                            frame,
                            (
                                int(self.collisionPoints[i][0]),
                                int(self.collisionPoints[i][1]),
                            ),
                            (
                                int(self.predictedPoints[i][0]),
                                int(self.predictedPoints[i][1]),
                            ),
                            (255, 255, 0),
                            thickness=2,
                            lineType=4,
                        )

        if self.showDebugImages:
            self.updateImageFromFrame(self.cameraImageLabel, frame)

        return frame

    def updatePreCalculationUi(self, frame, x, y, radius, robotX, robotY, robotRadius):
        # Update puck and robot values in the UI
        self.puckXLabel.setText(str(f"X: {x:.0f}"))
        self.puckYLabel.setText(str(f"Y: {y:.0f}"))
        self.puckRadiusLabel.setText(str(f"Radius: {radius:.0f}"))
        self.puckSpeedLabel.setText(str(f"Speed: {self.puckSpeed:.1f}"))

        self.robotXLabel.setText(str(f"X: {robotX:.0f}"))
        self.robotYLabel.setText(str(f"Y: {robotY:.0f}"))
        self.robotRadiusLabel.setText(str(f"Radius: {robotRadius:.0f}"))

        return frame

    def initializeCamera(self):
        try:
            self.currentFrameTimestamp = datetime.now()

            # Current camera image
            frame = self.camera.get_current_frame()

            # Check if corners of the camera image have been set
            if self.data.cornersApplied:
                # Input corners clockwise
                selectedCorners = np.float32(
                    [
                        [self.data.croppedTableCoords[0][0], self.data.croppedTableCoords[0][1]],
                        [self.data.croppedTableCoords[1][0], self.data.croppedTableCoords[1][1]],
                        [self.data.croppedTableCoords[2][0], self.data.croppedTableCoords[2][1]],
                        [self.data.croppedTableCoords[3][0], self.data.croppedTableCoords[3][1]],
                    ]
                )

                # Calculate transformation matrix (to apply a perspective transformation to the image)
                matrix = cv2.getPerspectiveTransform(
                    selectedCorners, self.data.originalCorners
                )

                # Apply perspective transformation
                frame = cv2.warpPerspective(
                    frame, matrix, (CAMERA_FRAME_HEIGHT, CAMERA_FRAME_WIDTH)
                )

            # Select corners of the camera image if they aren't set
            if not self.data.cornersApplied:
                for corner in self.croppedTableCoords:
                    cv2.circle(frame, (corner[0], corner[1]), 5, (255, 255, 255), 2)

            self.data.frameCounter = self.data.frameCounter + 1

            return frame
        except Exception as e:
            print("Couldn't process frame!")
            print(e)
            self.camera.stop()
            return None

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
