import serial
import cv2
import time
import random
from Constants import constants


class MoveMotor:
    def __init__(self, processPuckHSV=0):
        self.process_puck = processPuckHSV
        self.arduino = serial.Serial(port="COM4", baudrate=115200, timeout=0.1)
        self.center = (0, 0)
        self.movement_allowed = True
        self.old_motor_height = 0
        self.old_motor_width = 0
        self.old_random = 0

    # calibrate the robot
    def calibrate(self):
        time.sleep(5)
        self.arduino.write(bytes("calibrate\n", "utf-8"))
        time.sleep(5)

    # move to certain location(x, y)
    def move_x_y_absolute(self, width, height):
        motor_width, motor_height = self._real_to_motor(width, height)
        string = str(motor_height) + "," + str(motor_width)
        self.arduino.write(bytes(string, "utf-8"))
        time.sleep(2)

    # Calculate the values you have to send the motor, when you get real pixel values
    def _real_to_motor(self, width, height):
        multiplier_width = constants.MOTOR_WIDTH / constants.FIELD_WIDTH
        motor_coordinate_width = int(width * multiplier_width)
        multiplier_height = constants.MOTOR_HEIGHT / constants.FIELD_HEIGHT
        motor_coordinate_height = int(height * multiplier_height)
        return (motor_coordinate_width, motor_coordinate_height)

    def testMove(self):
        time.sleep(5)
        self.arduino.write(bytes("calibrate", "utf-8"))
        time.sleep(5)

        amountOfFrames = self.read_position()
        while amountOfFrames == 0:
            amountOfFrames = self.read_position()

        while True:
            
            if cv2.waitKey(1) == ord("q"):
                break
            amountOfFrames = self.read_position()
            if amountOfFrames == 0:
                continue
            #time.sleep(0.5)
            print(self.center[0], self.center[1])
            multiplier_width = constants.MOTOR_WIDTH / constants.FIELD_WIDTH
            motor_coordinate_width = (self.center[1]) * multiplier_width
            motor_coordinate_width = int(motor_coordinate_width)
            motor_coordinate_width = round(motor_coordinate_width, -2)
            #if self.center[0] > constants.FIELD_HEIGHT * 0.4:
            #    if self.old_motor_height > 1850 and self.old_motor_height < 2150:
            #            motor_coordinate_height = 4000
            #    else:
            #        motor_coordinate_height = 2000
            #else:
            multiplier_height = constants.MOTOR_HEIGHT / constants.FIELD_HEIGHT
            motor_coordinate_height = (self.center[0]) * multiplier_height
            motor_coordinate_height = int(motor_coordinate_height)
            motor_coordinate_height = round(motor_coordinate_height, -2)


            if motor_coordinate_height > self.old_motor_height - 150 and motor_coordinate_height < self.old_motor_height + 150:
               motor_coordinate_height += 300
            if motor_coordinate_width > self.old_motor_width - 50 and motor_coordinate_width < self.old_motor_width + 50:
                continue
                motor_coordinate_width += 50
            print(motor_coordinate_width)
            print(motor_coordinate_height)
            rnd_value = 2000 + round(int(random.random() * 4000), -2)
            while rnd_value == self.old_random:
                rnd_value = 2000 + round(int(random.random() * 4000), -2)
            if motor_coordinate_height < 10000:
                string = str(motor_coordinate_height) + "," + str(motor_coordinate_width)
            else:
                string = str(3000) + "," + str(motor_coordinate_width)
            # string = "random"


            stop = False
            while stop is False:
                self.arduino.write(bytes("ready\n", "utf-8"))
                data = self.arduino.readline()
                print(data)
                if data == b'bewegt':
                        #print (string)
                        self.arduino.write(bytes(string + "\n", "utf-8"))
                        self.old_random = rnd_value
                        self.old_motor_width = motor_coordinate_width
                        stop = True
                else:
                    break
            #if stop is False:
            #    continue

            #self.arduino.write(bytes(string, "utf-8"))
            #self.old_motor_height = motor_coordinate_height
            #self.old_motor_width = motor_coordinate_width
            #time.sleep(4)
            # data = arduino.readline()

    def loop(self):
        while True:
            num = input("Enter a string: ")  # Taking input from user
            value = self.write_loop(num)
            value = self.write_loop("5000,8000")
            print(value)  # printing the value

    def write_loop(self, x):
        stop = False
        while stop is False:
            self.arduino.write(bytes("ready\n", "utf-8"))
            data = self.arduino.readline()
            print(data)
            if data == b'True':
                    print (x)
                    self.arduino.write(bytes(x + "\n", "utf-8"))
                    stop = True
            else: 
                time.sleep(2)
        data = self.arduino.readline()
        return data
    
    def write(self, x):
        self.arduino.write(bytes(x + "\n", "utf-8"))
        time.sleep(3)
        data = self.arduino.readline()
        return data

    # def write(x):
    #   arduino.write(bytes(x, 'utf-8'))
    #  time.sleep(0.05)
    # data = arduino.readline()
    # return data
    # while True:
    #   num = input("Enter a string: ") # Taking input from user
    #  value = write(num)
    # print(value) # printing the value

    def read_position(self):
        position, amount_of_frames = self.process_puck.read_position()
        if amount_of_frames == 0:
            return amount_of_frames
        else:
            self.center = position
            return amount_of_frames

    def read_position_and_image(self):
        img, position, amount_of_frames = self.process_puck.read_position_and_image()
        if amount_of_frames == 0:
            return img, amount_of_frames
        else:
            self.center = position
            return img, amount_of_frames


if __name__ == "__main__":
    pass

    test = MoveMotor()
    test.calibrate()
    test.loop()

    print("EXIT")
    exit
