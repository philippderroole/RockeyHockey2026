#include <Arduino.h>
#include <AccelStepper.h>
#include "defines.h"
#include "calibration.h"
AccelStepper stepperx(1, MOTOR_X_STEP_PIN, MOTOR_X_DIR_PIN);
AccelStepper steppery(1, MOTOR_Y_STEP_PIN, MOTOR_Y_DIR_PIN);
bool st_enabled = false;
void setup() {
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(END_PIN_X, INPUT_PULLUP);
  pinMode(END_PIN_Y, INPUT_PULLUP);
  stepperx.setPinsInverted(false, false, true);
  steppery.setPinsInverted(false, false, true);
  SetStepperSettings();
  stepperx.setEnablePin(ENABLE_PIN);
  steppery.setEnablePin(ENABLE_PIN);
  Serial.begin(115200);
  calibrate();
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
void SetStepperSettings() {
  stepperx.setMaxSpeed(MAX_SPEED);
  stepperx.setAcceleration(MAX_ACCEL);
  stepperx.setSpeed(MIN_SPEED);
  steppery.setMaxSpeed(MAX_SPEED);
  steppery.setAcceleration(MAX_ACCEL_Y);
  steppery.setSpeed(MIN_SPEED);
}
void loop() {
  if (!st_enabled) {
    enable_steppers();
  }
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (strcmp(command.c_str(), "MAXIMA") == 0) {
      Serial.println(String(MAX_X) + "," + String(MAX_Y));
    } else if (strcmp(command.c_str(), "POSITION") == 0) {
      Serial.println(String(stepperx.currentPosition()) + "," + String(steppery.currentPosition()));
    } else if (strcmp(command.c_str(), "CALIBRATE") == 0) {
      calibrate();
    } else if (strcmp(command.c_str(), "STATUS") == 0) {
      if (stepperx.isRunning() || steppery.isRunning())
        Serial.println("BUSY");
      else
        Serial.println("READY");
    } else {
      int delimiterIndex = command.indexOf(',');
      long movement_x = command.substring(0, delimiterIndex).toInt();   //new x pos
      long movement_y = command.substring(delimiterIndex + 1).toInt();  //new y pos
      if (movement_x >= 0 && movement_x <= MAX_X && movement_y >= 0 && movement_y <= MAX_Y) {
        SetStepperSettings();
        stepperx.runToNewPosition(movement_x);
        steppery.runToNewPosition(movement_y);
      }
      Serial.println("OK");
    }
  }
}
