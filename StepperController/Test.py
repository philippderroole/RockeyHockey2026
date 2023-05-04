import time

from StepperController import StepperController
controller = StepperController("COM3", 115200)
controller.connect()
controller.calibrate()
controller.move_to_position(100,100)
time.sleep(1)
controller.move_to_position(1000,1000)
time.sleep(1)
controller.move_to_position(100,100)
