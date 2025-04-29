from Constants import *
import numpy as np
import math
from collections import deque
from Processing.Line import Line
from datetime import datetime
class DataModel: 
    def __init__(self):
        self.skippedPositions = 0
        # Coordinates to crop the camera image to fit the table.
        self.croppedTableCoords = [
            (TABLE_CORNER_TOP_LEFT_X, TABLE_CORNER_TOP_LEFT_Y),
            (TABLE_CORNER_TOP_RIGHT_X, TABLE_CORNER_TOP_RIGHT_Y),
            (TABLE_CORNER_BOTTOM_RIGHT_X, TABLE_CORNER_BOTTOM_RIGHT_Y),
            (TABLE_CORNER_BOTTOM_LEFT_X, TABLE_CORNER_BOTTOM_LEFT_Y),
        ]
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
        self.lastCollisionPoint = (0, 0)
        self.reflectionLine = Line((0, 0), (0, 0))
        self.puckCollides = False
        self.savedPoint = (0, 0)
        self.savedPoints = []
        self.preTargetPointX = (0, 0)
        self.targetPoint = (0, 0)
        self.lastMovePosition = (0, 0)
        self.wentBackToGoal = False
        self.attacked = False
        self.testTime = datetime.now()
        self.currentFrameTimestamp = datetime.now()
        self.lastFrameTimestamp = datetime.now()

model = DataModel()