#include <Arduino.h>
#include <AccelStepper.h>
#include "defines.h"
#include "calibration.h"
AccelStepper stepperx(1, MOTOR_X_STEP_PIN, MOTOR_X_DIR_PIN);
AccelStepper steppery(1, MOTOR_Y_STEP_PIN, MOTOR_Y_DIR_PIN);
bool st_enabled = false;
long movement_x = -1;
long movement_y = -1;
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

void loop() {
  if ((stepperx.distanceToGo() != 0) || (steppery.distanceToGo() != 0) && !st_enabled) {
    enable_steppers();
  }
  while ((stepperx.distanceToGo() != 0 || steppery.distanceToGo() != 0)) {
    if (!st_enabled) {
      enable_steppers();
    }
    if (stepperx.distanceToGo() != 0 && stepperx.targetPosition() <= MAX_X &&  stepperx.targetPosition()>=0) {
      stepperx.run();
    }
    if (steppery.distanceToGo() != 0 && steppery.targetPosition() <= MAX_Y &&  steppery.targetPosition()>=0) {
      steppery.run();
    }
  }
  if (stepperx.distanceToGo() == 0 && steppery.distanceToGo() == 0 && st_enabled) {
    //disable_steppers();
  }
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if(strcmp(command.c_str(), "MAXIMA") == 0){
      Serial.print(MAX_X);
      Serial.print(",");
      Serial.println(MAX_Y);
    }else if(strcmp(command.c_str(), "POSITION") == 0) {
      Serial.print(stepperx.currentPosition());
      Serial.print(",");
      Serial.println(steppery.currentPosition());
    } else if (strcmp(command.c_str(), "CALIBRATE") == 0){
      movement_x = 0;
      movement_y = 0;
      calibrate_x();
      calibrate_y();
      Serial.println("OK");
    }else if(strcmp(command.c_str(), "STATUS") == 0) {
      if(stepperx.isRunning()||steppery.isRunning())
      Serial.println("BUSY");
      else
      Serial.println("READY");
    } else {
      int delimiterIndex = command.indexOf(',');
      movement_x = command.substring(0, delimiterIndex).toInt();
      movement_y = command.substring(delimiterIndex + 1).toInt();
      Serial.println("OK");
    }
    stepperx.moveTo(movement_x);
    steppery.moveTo(movement_y);
  }
}
