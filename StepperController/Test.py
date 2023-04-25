import time

from StepperController import StepperController
controller = StepperController("COM3", 115200)
controller.connect()
controller.calibrate()
controller.move(100,100)
time.sleep(10)