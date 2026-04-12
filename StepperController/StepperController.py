import serial
import time
from queue import Queue
from PyQt5.QtCore import QThread
from enum import Enum
from Constants import *

class StepperController:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.camRobotPositionX = 0
        self.camRobotPositionY = 0
        self.syncRobotPosition = False

    def connect(self):
        # Open connection
        self.connection = serial.Serial(self.port, self.baudrate, timeout=1)
        
        # Wake up GRBL
        self.connection.write(b"\r\n\r\n")
        time.sleep(2)  # Wait for GRBL to initialize
        self.connection.reset_input_buffer()
        
        # Unlock GRBL
        self.send_command("$X")
        print("Connected to GRBL and unlocked.")

    def send_command(self, command):
        """Helper to send a G-Code string and wait for the 'ok' receipt."""
        self.connection.write((command + '\n').encode('utf-8'))
        
        # Wait for the "ok" response from GRBL
        while True:
            response = self.connection.readline().decode('utf-8').strip()
            if response == 'ok':
                return response
            elif response.startswith('error'):
                print(f"GRBL Error: {response}")
                return response

    def wait_for_idle(self):
        """Polls GRBL until the motors physically finish moving."""
        while True:
            self.connection.write(b"?") # '?' gets real-time status
            response = self.connection.readline().decode('utf-8').strip()
            
            # If GRBL reports it is idle, the movement is completely finished
            if response.startswith("<Idle"):
                break
            time.sleep(0.05) # Check again in 50ms

    def move_to_position(self, x, y):
        # Send absolute positioning G-Code
        command = f"G0 X{x} Y{y}"
        self.send_command(command)
        
        # Block the script until the physical movement finishes
        self.wait_for_idle()
        print(f"Moved to {x},{y}")
        return "OK"

    def calibrate(self):
        """Triggers GRBL's built-in homing cycle."""
        print("Homing machine...")
        self.send_command("$H")
        self.wait_for_idle()
        
        # After homing, set this position as Absolute Zero (0,0)
        self.send_command("G92 X0 Y0")
        print("Homing complete.")
        return "OK"

    def set_offset(self, x, y):
        """Uses Relative Coordinates to jog the machine."""
        command = f"G91\nG0 X{x} Y{y}\nG90"
        self.send_command(command)
        self.wait_for_idle()

    def updateRobotPos(self, x, y, syncRobotPosition):
        moveX = TABLE_MAX_X - x
        self.camRobotPositionX = int(moveX)    
        self.camRobotPositionY = int(y)
        self.syncRobotPosition = syncRobotPosition
        if syncRobotPosition:
            print('synchRobotPosition=True')

    def disconnect(self):
        if self.connection:
            self.connection.close()

class MoveType(Enum):
    NORMAL = 1
    CALIBRATE = 2

class MoveWorker(QThread):
    def __init__(self, stepperController, parent=None):
        super().__init__(parent)
        self.queue = Queue()
        self.stepperController = stepperController

    def run(self):
        while True:
            type, x, y = self.queue.get()
            if self.stepperController is not None:
                if type == MoveType.NORMAL:
                    self.stepperController.move_to_position(int(x), int(y))
                elif type == MoveType.CALIBRATE:
                    self.stepperController.calibrate()

    def set_values(self, type, x, y):
        self.queue.put((type, x, y))