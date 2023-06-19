import serial
import time
from queue import Queue
from threading import Thread


class StepperController(Thread):
    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.position_queue = Queue()

    def run(self):
        self.connect()
        while True:
            if not self.position_queue.empty():
                x, y = self.position_queue.get()
                self.move_to_position(x, y)
            else:
                # No position in the queue, do something else or wait
                time.sleep(1)
                continue
        self.disconnect()

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

    def enqueue_position(self, x, y):
        self.position_queue.put((x, y))

    def disconnect(self):
        self.connection.close()
