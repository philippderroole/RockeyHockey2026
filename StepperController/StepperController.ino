#include <Arduino.h>
#include <AccelStepper.h>
#include "defines.h"
#include "calibration.h"
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
void enable_steppers() {
  if (!st_enabled) {
    stepperx.enableOutputs();
    steppery.enableOutputs();
    st_enabled = true;
  }
}
void disable_steppers() {
  if (st_enabled) {
    stepperx.disableOutputs();
    steppery.disableOutputs();
    st_enabled = false;
  }
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
    enable_steppers();
  }
  while ((stepperx.distanceToGo() != 0 || steppery.distanceToGo() != 0)) {
    if (!st_enabled) {
      enable_steppers();
    }
    if (stepperx.distanceToGo() != 0 && moveAllowedX()) {
      stepperx.runSpeedToPosition();
    }
    if (steppery.distanceToGo() != 0 && moveAllowedY()) {
      steppery.runSpeedToPosition();
    }
  }
  if (stepperx.distanceToGo() == 0 && steppery.distanceToGo() == 0 && st_enabled) {
    disable_steppers();
  }
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if(strcmp(command.c_str(), "maximum") == 0){
      Serial.print(MAX_X);
      Serial.print(",");
      Serial.println(MAX_Y);
    }else if(strcmp(command.c_str(), "position") == 0) {
      Serial.print(stepperx.currentPosition());
      Serial.print(",");
      Serial.println(steppery.currentPosition());
    } else if (strcmp(command.c_str(), "calibrate") == 0){
      movement_x = 0;
      movement_y = 0;
      calibrate_x();
      calibrate_y();
      movement_x = MAX_X / 2;
      movement_y = MAX_Y / 2;
    }else if(strcmp(command.c_str(), "status") == 0) {
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
