from StepperController import *
import time

if __name__ == "__main__":
    
    controller = None
    # Use "MOCK" for testing without hardware
    port = "MOCK" 
    baudrate = "115200"

    print(f"--- Starting StepperController Test on {port} ---")

    try:
        controller = StepperController(port, baudrate)
        
        print("\n1. Testing connect()...")
        controller.connect()
        
        print("\n2. Testing send_command()...")
        # Send a harmless command to check communication
        response = controller.send_command("$I")
        print(f"Response: {response}")

        print("\n3. Testing calibrate()...")
        controller.calibrate()
        controller.move_to_position(20, 180)     


        print("\n4. Testing move_to_position()...")
        controller.move_to_position(170, 10)
        controller.move_to_position(180, 350)
        controller.move_to_position(250, 100)
        controller.move_to_position(20, 0)
        controller.move_to_position(200, 300)
        controller.cancel_jog()
        controller.move_to_position(180, 100)
        controller.move_to_position(20, 180)
        
        print("\n5. Testing wait_for_idle()...")
        controller.wait_for_idle()
        print("Machine is idle.")

        print("\n6. Testing cancel_jog()...")
        controller.move_to_position(10, 10)
        controller.cancel_jog()
        print("Jog cancelled.")

        print("\n7. Testing disconnect()...")
        controller.disconnect()

        print("\n--- StepperController methods tested successfully ---")

    except Exception as e:
        print(f"\nERROR during testing: {e}")
        if controller:
            controller.disconnect()
