import serial


class StepperController:
    def __init__(self, port, baud):
        self.ser = serial.Serial(port, baud)
        self.ser.open()

    def move_to_position(self, x, y):
        self.ser.write(str(x) + "," + str(y) + "\n")

    def get_current_position(self):
        self.ser.write("position\n")
        tmp = self.ser.readline()
        tmp = tmp.split(",")
        return {int(tmp[0]), int(tmp[1])}

    def get_controller_status(self):
        self.ser.write("status\n")
        return self.ser.readline()

    def calibrate(self):
        self.ser.write("calibrate\n")

    def close(self):
        self.ser.close()
