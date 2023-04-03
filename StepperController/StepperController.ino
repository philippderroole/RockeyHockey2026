#include <Arduino.h>
#include <AccelStepper.h>
#include "defines.h"
AccelStepper stepperx(1, MOTOR_X_STEP_PIN, MOTOR_X_DIR_PIN);
AccelStepper steppery(1, MOTOR_Y_STEP_PIN, MOTOR_Y_DIR_PIN);
bool st_enabled = false;
long movement_x = 0;
long movement_y = 0;
void setup() {
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(END_PIN_X, INPUT_PULLUP);
  pinMode(END_PIN_Y, INPUT_PULLUP);
  stepperx.setPinsInverted(false, false, true);
  steppery.setPinsInverted(false, false, true);
  stepperx.setMaxSpeed(MAX_SPEED);
  stepperx.setAcceleration(MAX_ACCEL);
  stepperx.setSpeed(MIN_SPEED);
  steppery.setMaxSpeed(MAX_SPEED);
  steppery.setAcceleration(MAX_ACCEL);
  steppery.setSpeed(MIN_SPEED);
  stepperx.setEnablePin(ENABLE_PIN);
  steppery.setEnablePin(ENABLE_PIN);
  Serial.begin(115200);
}
void calibrate_x() {
  long homing = -1;
  stepperx.enableOutputs();
  Serial.println("Calibrate X");
  while (digitalRead(END_PIN_X)) {
    stepperx.moveTo(homing);
    homing--;
    delay(5);
    stepperx.run();
  }
  stepperx.setCurrentPosition(0);
  stepperx.setMaxSpeed(MAX_SPEED);
  stepperx.setAcceleration(MAX_ACCEL);
  stepperx.disableOutputs();
}
void calibrate_y() {
  long homing = -1;
  steppery.enableOutputs();
  Serial.println("Calibrate Y");
  while (digitalRead(END_PIN_Y)) {
    steppery.moveTo(homing);
    delay(5);
    homing--;
    steppery.run();
  }
  steppery.setCurrentPosition(0);
  steppery.setMaxSpeed(MAX_SPEED);
  steppery.setAcceleration(MAX_ACCEL);
  steppery.disableOutputs();
}
void calibrate(){
  calibrate_x();
  calibrate_y();
  Serial.println("ready");
}
void GoToStartPosition() {
  movement_x = MAX_X / 2;
  movement_y = MAX_Y / 2;
}
bool moveAllowedY() {
  if (digitalRead(END_PIN_Y) == 0) {
    if (steppery.distanceToGo() > 0) {
      return true;
    } else {
      steppery.stop();
      steppery.setCurrentPosition(0);
      return false;
    }
  } else if (steppery.targetPosition() > MAX_Y) {
    steppery.stop();
    return false;
  } else {
    return true;
  }
}
bool moveAllowedX() {
  if (digitalRead(END_PIN_X) == 0) {
    if (stepperx.distanceToGo() > 0) {
      return true;
    } else {
      stepperx.stop();
      stepperx.setCurrentPosition(0);
      return false;
    }
  } else if (stepperx.targetPosition() > MAX_X) {
    stepperx.stop();
    return false;
  } else {
    return true;
  }
}
void loop() {
  if ((stepperx.distanceToGo() != 0) || (steppery.distanceToGo() != 0) && !st_enabled) {
    st_enabled = true;
    stepperx.enableOutputs();
    steppery.enableOutputs();
  }
  while ((stepperx.distanceToGo() != 0 || steppery.distanceToGo() != 0)) {
    if (!st_enabled) {
      st_enabled = true;
      stepperx.enableOutputs();
      steppery.enableOutputs();
    }
    if (stepperx.distanceToGo() != 0 && moveAllowedX()) {
      stepperx.runSpeedToPosition();
    }
    if (steppery.distanceToGo() != 0 && moveAllowedY()) {
      steppery.runSpeedToPosition();
    }
  }
  if (stepperx.distanceToGo() == 0 && steppery.distanceToGo() == 0 && st_enabled) {
    st_enabled = false;
    stepperx.disableOutputs();
    steppery.disableOutputs();
  }
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if((command == "maximum\n")||(command == "maximum")){
      Serial.print(MAX_X);
      Serial.print(",");
      Serial.println(MAX_Y);
    }else if ((command == "position\n") || (command == "position")) {
      Serial.print(stepperx.currentPosition());
      Serial.print(",");
      Serial.println(steppery.currentPosition());
    } else if ((command == "calibrate\n") || (command == "calibrate")) {
      movement_x = 0;
      movement_y = 0;
      calibrate_x();
      calibrate_y();
      GoToStartPosition();
    }else if((command == "status") || (command == "status\n")){
      if(stepperx.isRunning()||steppery.isRunning())
      Serial.println("busy");
      else
      Serial.println("ready");
    } else {
      int delimiterIndex = command.indexOf(',');
      movement_x = command.substring(0, delimiterIndex).toInt();
      movement_y = command.substring(delimiterIndex + 1).toInt();
    }
    stepperx.moveTo(movement_x);
    steppery.moveTo(movement_y);
  }
}
