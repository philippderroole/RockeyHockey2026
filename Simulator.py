# Written by Lukas Karg 2023
import sys
import time

import numpy as np
import qdarkstyle
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSplashScreen, QApplication
from Processing.Line import *
import cv2

WINDOW_TITLE = "HockeySimulator"
HOCKEY_TABLE_HEIGHT = 600
HOCKEY_TABLE_WIDTH = 350
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


app = QApplication(sys.argv)
app.setStyleSheet(qdarkstyle.load_stylesheet())
splash = QSplashScreen(QPixmap("splash.png"))
splash.show()
time.sleep(0.5)
splash.close()
cv2.namedWindow(WINDOW_TITLE)
cv2.createTrackbar("Robot Y:", WINDOW_TITLE, 0, int(HOCKEY_TABLE_HEIGHT / 2), on_trackbar)
# Draw Table
hockey_table = np.zeros((HOCKEY_TABLE_HEIGHT, HOCKEY_TABLE_WIDTH, 3), dtype=np.uint8)
cv2.line(hockey_table, (0, int(HOCKEY_TABLE_HEIGHT / 2)), (HOCKEY_TABLE_WIDTH, int(HOCKEY_TABLE_HEIGHT / 2)),
         (255, 255, 255))
cv2.rectangle(hockey_table, ((HOCKEY_TABLE_WIDTH // 2) - 40, 0), ((HOCKEY_TABLE_WIDTH // 2) + 40, 10), (255, 255, 255),
              2)
cv2.rectangle(hockey_table, ((HOCKEY_TABLE_WIDTH // 2) - 40, HOCKEY_TABLE_HEIGHT - 10),
              ((HOCKEY_TABLE_WIDTH // 2) + 40, HOCKEY_TABLE_HEIGHT), (255, 255, 255), 2)
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
    cv2.line(frame, puck_pos, user_pos, (255, 20, 255), thickness=1, lineType=4)
    reflected = False
    line = Line(user_pos, puck_pos)
    if line.get_m() is not None:
        if line.get_angle() >= 0:  # left edge
            collision_point = (int(0), int(line.get_y(0)))
        else:  # right edge
            collision_point = (int(HOCKEY_TABLE_WIDTH), int(line.get_y(HOCKEY_TABLE_WIDTH)))
        if collision_point[1] > robot_pos[1]:  # reflection is disabled if point is behind robot
            if line.get_m() is not None:
                reflection_line = Line(collision_point, None, (1 / line.get_m()))
                reflection_point = (int(HOCKEY_TABLE_WIDTH - reflection_line.get_x(robot_pos[0])), int(robot_pos[1]))
                cv2.circle(frame, reflection_point, HOCKEY_PUCK_RADIUS, (100, 0, 255), -1)
                cv2.line(frame, puck_pos, collision_point, (255, 255, 255), thickness=1, lineType=4)
                cv2.line(frame, collision_point, reflection_point, (255, 255, 255), thickness=1, lineType=4)
                cv2.circle(frame, collision_point, HOCKEY_PUCK_RADIUS, (0, 100, 255), -1)
    if line.get_m() is not None:
        final_point = (int(line.get_x(robot_pos[1])), int(robot_pos[1]))  # normal line prediction
        cv2.circle(frame, final_point, HOCKEY_PUCK_RADIUS, (100, 0, 255), -1)
        cv2.line(frame, puck_pos, final_point, (255, 255, 255), thickness=1, lineType=4)
    cv2.imshow(WINDOW_TITLE, frame)
    cv2.setMouseCallback(WINDOW_TITLE, mouse_event_handler)
    if cv2.waitKey(10) == 27:  # exit if ESC is pressed
        break
    if cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:  # regular window close
        break
cv2.destroyAllWindows()
