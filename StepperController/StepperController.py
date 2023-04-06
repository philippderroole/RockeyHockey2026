import serial
import time


class StepperController:
    def __init__(self, port, baud):
        self.ser = serial.Serial(port, baud)
        self.ser.open()
        time.sleep(3)
        self.writeline("maximum")
        tmp = self.readline().split(",")
        self.max_x, self.max_y = int(tmp[0]), int(tmp[1])

    def readline(self):
        return self.ser.readline().decode('utf-8').rstrip()

    def writeline(self, line):
        self.ser.write(line + "\n")

    def move_to_position(self, x, y):
        if 0 <= x <= self.max_x and 0 <= y <= self.max_y:
            self.writeline(str(x) + "," + str(y))

    def get_current_position(self):
        self.writeline("position")
        tmp = self.readline().split(",")
        return {int(tmp[0]), int(tmp[1])}

    def get_status(self):
        self.writeline("status")
        return self.readline()

    def get_max_x(self):
        return self.max_x

    def get_max_y(self):
        return self.max_y

    def calibrate(self):
        self.writeline("calibrate")
        self.ser.readline()

    def close(self):
        self.ser.close()
