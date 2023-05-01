import serial
import time


class StepperController:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connection = None

    def connect(self):
        self.connection = serial.Serial(self.port, self.baudrate, timeout=1)
        time.sleep(2)  # wait for the Arduino to reset
        self.connection.flushInput()

    def move_to_position(self, x, y):
        command = str(x) + ',' + str(y) + '\n'
        self.connection.write(command.encode())
        response = self.connection.readline().decode().strip()
        return response

    def calibrate(self):
        self.connection.write(b'CALIBRATE\n')
        response = self.connection.readline().decode().strip()
        return response

    def get_status(self):
        self.connection.write(b'STATUS\n')
        response = self.connection.readline().decode().strip()
        return response

    def get_position(self):
        self.connection.write(b'POSITION\n')
        response = self.connection.readline().decode().strip()
        x, y = response.split(',')
        return int(x), int(y)

    def get_maxima(self):
        self.connection.write(b'MAXIMA\n')
        response = self.connection.readline().decode().strip()
        x, y = response.split(',')
        return int(x), int(y)

    def disconnect(self):
        self.connection.close()
