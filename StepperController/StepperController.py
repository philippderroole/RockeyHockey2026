import serial
import time
from queue import Queue
from threading import Thread


class StepperController():
    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.position_queue = Queue()

    def connect(self):
        self.connection = serial.Serial(self.port, self.baudrate, timeout=1)
        time.sleep(2)  # wait for the Arduino to reset
        self.connection.flushInput()

    def move_to_position(self, x, y):
        command = str(x) + ',' + str(y) + '\n'
        self.connection.write(command.encode())
        response = self.connection.readline().decode().strip()
        return response

    def set_offset(self, x, y):
        if x >= 0:
            x_offset = "+"
        else:
            x_offset = "-"
        x_offset += str(x) + '\n'
        if y >= 0:
            y_offset = "+"
        else:
            y_offset = "-"
        y_offset += str(y) + '\n'
        if y != 0:
            self.connection.write(b'OFFSETY'+y_offset.encode())
            self.connection.readline()
        if x != 0:
            self.connection.write(b'OFFSETX'+x_offset.encode())
            self.connection.readline()

    def calibrate(self):
        self.connection.write(b'CALIBRATE\n')
        response = self.connection.readline().decode().strip()
        return response

    def disconnect(self):
        self.connection.close()
