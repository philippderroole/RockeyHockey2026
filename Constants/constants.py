# ------------- DIMENSIONS -------------
# Field dimensions in game units
# -----
# |   |
# |   | <- height (x)
# |   |
# -----
# <   > <- width (y)
# Real-Life:
# Height = 162cm
# Width = 92,5cm
# Goal = ...cm
FIELD_WIDTH = 925
FIELD_HEIGHT = 1620
GOAL_SPAN = 240
CHAMBER_SIZE = 30  # on both size - eg: 30 = 30mm x 30mm

# Motor dimensions
MOTOR_WIDTH = 15700
MOTOR_HEIGHT = 22000
# Objects sizes in game units
PUCK_RADIUS = 31
STRIKER_RADIUS = 50

# Field dimensions for path prediction
FIELD_WIDTH_PATH = FIELD_WIDTH - (2 * PUCK_RADIUS)
FIELD_HEIGHT_PATH = FIELD_HEIGHT - (2 * PUCK_RADIUS)

# Limits
YLIMIT = 230
XLIMIT = 65
STRIKER_AREA_WIDTH = 446

# -------------- Aruco --------------
PUCK_ARUCO_ID = 0
