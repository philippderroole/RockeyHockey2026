from StepperController import *
import time

# Run from root project directory with: python -m StepperController.test_worker, because of Constants.py dependency

if __name__ == "__main__":
    controller = None
    worker = None

    port = "COM3"
    baudrate = "115200"

    print("--- Testing Normal vs Immediate Move Behavior ---")
    print(f"Port: {port}\n")

    try:
        controller = StepperController(port, baudrate)
        controller.connect()
        print()

        worker = MoveWorker(controller)
        worker.start()
        time.sleep(0.1)

        print("=== Calibration first ===")
        print("  Homing and moving to home position...")
        worker.set_values(MoveType.CALIBRATE, HOME_POSITION_X, HOME_POSITION_Y)
        while not worker.queue.empty():
            time.sleep(0.1)
        time.sleep(3.0)
        print("  Calibration done\n")

        print("=== Test 1: NORMAL moves (queue behind each other) ===")
        print("  Sending 3 normal moves rapidly...")
        worker.set_values(MoveType.NORMAL, 10, 10)
        worker.set_values(MoveType.NORMAL, 50, 50)
        worker.set_values(MoveType.NORMAL, 100, 100)
        time.sleep(1.5)
        controller.read_output("?")
        print("  (should have only moved to pos3 — queue drained to latest)\n")

        
        print("=== Test 2: IMMEDIATE cancels current jog ===")
        print("  Sending a normal move then IMMEDIATE override...")
        worker.set_values(MoveType.NORMAL, 240, 240)
        worker.set_values(MoveType.IMMEDIATE, 20, 20)
        time.sleep(1.5)
        controller.read_output("?")
        print("  (should have cancelled 'far away' and moved to 20,20)\n")

        print("=== Test 3: IMMEDIATE move by itself ===")
        worker.set_values(MoveType.IMMEDIATE, 150, 150)
        time.sleep(1.0)
        controller.read_output("?")
        print("  (IMMEDIATE move completed)\n")
#
        print("=== Test 4: Queue draining under rapid fire ===")
        print("  Sending 10 moves in rapid succession...")
        for i in range(10):
            worker.set_values(MoveType.NORMAL, i * 10, i * 10)
        time.sleep(1.5)
        controller.read_output("?")
        print("  (should only execute the last one: 90,90)\n")
#
        print("=== Test 5: IMMEDIATE after rapid NORMAL ===")
        print("  Sending normal moves then IMMEDIATE interrupt...")
        for i in range(5):
            worker.set_values(MoveType.NORMAL, i * 30, i * 30)
        time.sleep(0.05)
        worker.set_values(MoveType.IMMEDIATE, 5, 5)
        time.sleep(1.5)
        controller.read_output("?")
        print("  (IMMEDIATE should cancel any running normal and jump to 5,5)\n")
#
        print("--- All tests completed ---")

        worker.terminate()
        controller.disconnect()

    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        if worker:
            worker.terminate()
        if controller:
            controller.disconnect()
