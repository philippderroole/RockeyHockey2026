from StepperController import StepperController
controller = StepperController("COM4", 115200)
print("MAXY=("+str(controller.get_max_x())+"|"+str(controller.get_max_y())+")")
controller.calibrate()
print("goto center")
controller.move_to_position(controller.get_max_x()/2, controller.get_max_y()/2)
