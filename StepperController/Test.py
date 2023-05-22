import time

from StepperController import StepperController
controller = StepperController("COM3", 115200)
controller.connect()
controller.calibrate()
while True:
    controller.move_to_position(0, 0)
    controller.move_to_position(1800, 1800)

