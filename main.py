from StepperController import StepperController
from Camera import Camera
controller = StepperController("COM4", 115200)
camera = Camera(0, 60)
