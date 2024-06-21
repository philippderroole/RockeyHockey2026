from StepperController import *
import time

if __name__ == "__main__":
    
    controller = None
    try:
            controller = StepperController("COM6", "115200")
            controller.connect()
    except Exception:
        print("ERROR: No Arduino found on " + "COM6" + ".")
        controller = None

    print(str(controller))
    #moveWorker = MoveWorker(controller)
    #moveWorker.start()
    #moveWorker.set_values("CALIBRATE", 100, 100)
    controller.calibrate()
    time.sleep(5)
    
    print(controller.move_to_position(925,100))
    controller.move_to_position(1000,1700)
    controller.move_to_position(100,100)
    controller.move_to_position(300,100)
    controller.move_to_position(1700,1700)
    controller.move_to_position(100,1700)
    controller.move_to_position(1700,100)
    controller.move_to_position(500,500)
    time.sleep(1)
    controller.move_to_position(925,100)


    
    #print("sadfasdf")
    #print(moveWorker.set_values("NORMAL", 925, 100))
    #moveWorker.set_values("NORMAL", 1700, 1700)
    #moveWorker.set_values("NORMAL", 100, 1700)
    #moveWorker.set_values("NORMAL", 100, 100)
    #moveWorker.set_values("NORMAL", 925, 100)
    

    # print(controller.attack(1700,1700))
    #moveWorker.set_values("ATTACK", 1000, 1000)
    # controller.move_to_position(925, 100)
    
    # controller.attack(1000,1000)