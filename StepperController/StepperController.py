import serial
import time


class StepperController:
    def __init__(self, port, baud):
        self.ser = serial.Serial(port, baud)
        self.ser.open()
        time.sleep(1)
        self.ser.write("maximum\n")
        tmp = self.ser.readline().split(",")
        self.max_x, self.max_y = int(tmp[0]), int(tmp[1])

    def move_to_position(self, x, y):
        self.ser.write(str(x) + "," + str(y) + "\n")
        self.ser.readline()

    def get_current_position(self):
        self.ser.write("position\n")
        tmp = self.ser.readline()
        tmp = tmp.split(",")
        return {int(tmp[0]), int(tmp[1])}

    def get_status(self):
        self.ser.write("status\n")
        return self.ser.readline()

    def get_max_x(self):
        return self.max_x

    def get_max_y(self):
        return self.max_y

    def calibrate(self):
        self.ser.write("calibrate\n")
        self.ser.readline()

    def close(self):
        self.ser.close()
