# Lukas Karg 2023
import numpy as np
from Processing.Line import *
import cv2
import math

WINDOW_TITLE = "HockeySimulator"
HOCKEY_TABLE_HEIGHT = 600
HOCKEY_TABLE_WIDTH = 300
HOCKEY_BAT_RADIUS = 10
HOCKEY_PUCK_RADIUS = 5

puck_pos = (0, 0)
puck_pos2 = (0, 0)
robot_pos = (0, 0)
user_pos = (0, 0)


def mouse_event_handler(event, x, y, flags, userdata):
    global user_pos
    if y > (HOCKEY_TABLE_HEIGHT / 2) + HOCKEY_BAT_RADIUS:
        user_pos = (x, y)


def on_trackbar(val):
    global robot_pos
    robot_pos = (int(HOCKEY_TABLE_WIDTH / 2), int(val))


def get_gradient(p1, p2):  # Steigung der Geraden
    dY = p2[1] - p1[1]
    dX = p2[0] - p1[0]
    result = 0
    if dX != 0:
        result = dY / dX
    return result


cv2.namedWindow(WINDOW_TITLE)
cv2.createTrackbar("Robot Y-Pos:", WINDOW_TITLE, 0, int(HOCKEY_TABLE_HEIGHT/2), on_trackbar)
# Draw Table
hockey_table = np.zeros((HOCKEY_TABLE_HEIGHT, HOCKEY_TABLE_WIDTH, 3), dtype=np.uint8)
cv2.line(hockey_table, (0, int(HOCKEY_TABLE_HEIGHT / 2)), (HOCKEY_TABLE_WIDTH, int(HOCKEY_TABLE_HEIGHT / 2)),
         (255, 255, 255))
# Convert image to 8-bit
hockey_table = cv2.convertScaleAbs(hockey_table)
puck_pos = (int(HOCKEY_TABLE_WIDTH / 2), int(HOCKEY_TABLE_HEIGHT / 2))
robot_pos = (int(HOCKEY_TABLE_WIDTH / 2), int(20))
user_pos = (int(HOCKEY_TABLE_WIDTH / 2), int(HOCKEY_TABLE_HEIGHT - 20))
while True:
    # Copy Table Board
    frame = hockey_table.copy()
    cv2.circle(frame, robot_pos, HOCKEY_BAT_RADIUS, (0, 255, 0), -1)
    cv2.circle(frame, user_pos, HOCKEY_BAT_RADIUS, (255, 0, 0), -1)
    cv2.circle(frame, puck_pos, HOCKEY_PUCK_RADIUS, (0, 0, 255), -1)
    cv2.line(frame, puck_pos, user_pos, (255, 255, 255), thickness=1, lineType=4)
    reflected = False
    if 0 <= puck_pos2[1] <= HOCKEY_TABLE_HEIGHT and 0 <= puck_pos2[0] <= HOCKEY_TABLE_WIDTH:
        line = Line(user_pos, puck_pos2)
        if line.get_angle() >= 0:  # left edge
            auf_point = (int(0), int(line.get_y(0)))
        else:  # right edge
            auf_point = (int(HOCKEY_TABLE_WIDTH), int(line.get_y(HOCKEY_TABLE_WIDTH)))
        if auf_point[1] > robot_pos[1]:  # reflection is disabled if point is behind robot
            try:
                reflection_line = Line(auf_point, None, (1 / line.get_m()))
                reflection_point = (int(HOCKEY_TABLE_WIDTH - reflection_line.get_x(robot_pos[0])), int(robot_pos[1]))
                cv2.circle(frame, reflection_point, HOCKEY_PUCK_RADIUS, (100, 0, 255), -1)
                cv2.line(frame, puck_pos, auf_point, (255, 255, 255), thickness=1, lineType=4)
                cv2.line(frame, auf_point, reflection_point, (255, 255, 255), thickness=1, lineType=4)
                cv2.circle(frame, auf_point, HOCKEY_PUCK_RADIUS, (0, 100, 255), -1)
            except:
                pass
        try:
            final_point = (int(line.get_x(robot_pos[1])), int(robot_pos[1]))
            cv2.circle(frame, final_point, HOCKEY_PUCK_RADIUS, (100, 0, 255), -1)
        except:
            pass
        b = HOCKEY_TABLE_HEIGHT / 2
        m = line.get_m()
        if m == 0:# puck_pos2 -> This simulates the second camera frame
            puck_pos2 = (int(HOCKEY_TABLE_WIDTH / 2), int(HOCKEY_TABLE_HEIGHT / 2 - 12))
        else:
            puck_pos2 = (int(((puck_pos2[1] - b) / m) + (HOCKEY_TABLE_WIDTH / 2)), int(HOCKEY_TABLE_HEIGHT / 2 - 12))
    else:
        puck_pos2 = (int(HOCKEY_TABLE_WIDTH / 2), int(HOCKEY_TABLE_HEIGHT / 2))
    cv2.circle(frame, puck_pos2, HOCKEY_PUCK_RADIUS, (0, 0, 255), -1)
    cv2.imshow(WINDOW_TITLE, frame)
    cv2.setMouseCallback(WINDOW_TITLE, mouse_event_handler)
    if cv2.waitKey(10) == 27:  # exit if ESC is pressed
        break
cv2.destroyAllWindows()
