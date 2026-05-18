import serial
import time
from queue import Queue, Empty
from PyQt5.QtCore import QThread
from enum import Enum

class MockSerial:
    """A fake serial port that pretends to be a GRBL Arduino."""
    def __init__(self, port, baudrate, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_open = True
        self.response_queue = []
        print(f"\n[MOCK HARDWARE] Virtual Arduino connected on {port}")

    def write(self, data):
        # Intercept real-time commands like Jog Cancel (0x85)
        if b'\x85' in data:
            print("[MOCK HARDWARE] Received Jog Cancel (0x85) - Aborting current move")
            data = data.replace(b'\x85', b'')
            if not data: return

        command = data.decode('utf-8', errors='ignore').strip()

        if command != "?":
            print(f"[MOCK HARDWARE] Received Command: {command}")

        if command == "?":
            self.response_queue.append(b"<Idle|MPos:0.000,0.000,0.000|FS:0,0>\n")
        elif command == "$$":
            self.response_queue.append(b"$0=10\n$1=25\n$2=0\n$3=0\n$4=0\n$5=0\n$6=0\n$10=1\n$11=0.010\n$12=0.002\n$13=0\n$20=0\n$21=0\n$22=1\n$23=0\n$24=25.000\n$25=500.000\n$26=250\n$27=1.000\n$30=1000\n$31=0\n$32=0\n$100=800.000\n$101=800.000\n$102=800.000\n$110=20000.000\n$111=20000.000\n$112=500.000\n$120=1000.000\n$121=1000.000\n$122=100.000\n$130=200.000\n$131=200.000\n$132=200.000\nok\n")
        elif command == "$G":
            self.response_queue.append(b"[GC:G0 G54 G17 G21 G90 G94 M5 M9 T0 F0 S0]\nok\n")
        elif command == "$I":
            self.response_queue.append(b"[VER:1.1f MOCK.20190825:]\n[OPT:V,15,128]\nok\n")
        elif command == "$#":
            self.response_queue.append(b"[G54:0.000,0.000,0.000]\n[G55:0.000,0.000,0.000]\n[G56:0.000,0.000,0.000]\n[G57:0.000,0.000,0.000]\n[G58:0.000,0.000,0.000]\n[G59:0.000,0.000,0.000]\n[G28:0.000,0.000,0.000]\n[G30:0.000,0.000,0.000]\n[G92:0.000,0.000,0.000]\n[TLO:0.000]\n[PRB:0.000,0.000,0.000:0]\nok\n")
        elif command in ["$X", "$H"] or command.startswith("G") or command.startswith("$J"):
            self.response_queue.append(b"ok\n")
        elif command == "":
            self.response_queue.append(b"ok\n")

    def readline(self):
        # Send the faked response back to the Python script
        if self.response_queue:
            return self.response_queue.pop(0)
        return b"" # Simulate a timeout if no response is queued

    @property
    def in_waiting(self):
        total = 0
        for item in self.response_queue:
            total += len(item)
        return total

    def reset_input_buffer(self):
        self.response_queue = []

    def close(self):
        self.is_open = False
        print("[MOCK HARDWARE] Connection closed.")

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
        if self.port == "MOCK":
            self.connection = MockSerial(self.port, self.baudrate, timeout=1)
        else:
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

        # Wait for the "ok" response from GRBL indicating it entered the buffer
        while True:
            response = self.connection.readline().decode('utf-8').strip()
            if response == 'ok':
                return response
            elif response.startswith('error'):
                print(f"GRBL Error: {response}")
                return response

    def wait_for_idle(self):
        """Polls GRBL until the motors physically finish moving. ONLY used for calibration."""
        while True:
            self.connection.write(b"?") # '?' gets real-time status
            response = self.connection.readline().decode('utf-8').strip()

            # If GRBL reports it is idle, the movement is completely finished
            if response.startswith("<Idle"):
                break
            time.sleep(0.05) # Check again in 50ms

    def cancel_jog(self):
        """
        Sends the real-time Jog Cancel command (0x85) to GRBL.
        This forces GRBL to safely decelerate to a stop and flush the buffer.
        """
        if self.connection:
            self.connection.write(b'\x85')

    def move_to_position(self, x, y, feedrate=25000):
        """
        Streams a jog movement command to GRBL without blocking.
        Allows immediate retargeting mid-movement.
        """
        # Abort any currently executing movement first
        self.cancel_jog()

        # Issue the new Jog command
        command = f"$J=G21G90X{x}Y{y}F{feedrate}"
        self.send_command(command)

    def calibrate(self):
        """Triggers GRBL's built-in homing cycle."""
        print("Homing machine...")
        self.send_command("$H")
        self.wait_for_idle()
        print("Homing complete.")
        return "OK"

    def read_output(self, command=None, timeout=0.5):
        if self.connection is None:
            print("[read_output] Not connected.")
            return

        if command is not None:
            print(f"[read_output] Sending: {command}")
            self.connection.write((command + '\n').encode('utf-8'))

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.connection.in_waiting > 0:
                line = self.connection.readline().decode('utf-8').strip()
                if line:
                    print(f"[GRBL] {line}")
            else:
                time.sleep(0.01)

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
            # Block until at least one target is added to the queue
            item = self.queue.get()

            while not self.queue.empty():
                try:
                    item = self.queue.get_nowait()
                except Empty:
                    break
            
            type, x, y = item
            
            if self.stepperController is not None:
                if type == MoveType.NORMAL:
                    self.stepperController.move_to_position(int(x), int(y))
                elif type == MoveType.CALIBRATE:
                    self.stepperController.calibrate()

    def set_values(self, type, x, y):
        self.queue.put((type, x, y))
