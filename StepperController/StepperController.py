import serial


class StepperController:
    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate)
        self.ser.open()

    def move_to_position(self, x, y):
        self.ser.write(x + "," + y + "\n")

    def get_current_position(self):
        self.ser.write("position\n")

    def close(self):
        self.ser.close()
