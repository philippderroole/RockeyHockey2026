#include <Arduino.h>
#include <AccelStepper.h>
#include <MultiStepper.h>
#include "defines.h"
#include "calibration.h"
AccelStepper stepperx(1, MOTOR_X_STEP_PIN, MOTOR_X_DIR_PIN);
AccelStepper steppery(1, MOTOR_Y_STEP_PIN, MOTOR_Y_DIR_PIN);
MultiStepper steppers;
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
  steppers.addStepper(stepperx);
  steppers.addStepper(steppery);
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
  int StartZeit = 0;
  if (!st_enabled) {
    enable_steppers();
  }

  if (Serial.available() > 0) {
    //StartZeit = millis();

    // Immer den neuesten Command nehmen der übertragen wurde
    String command = "";
    do {
      command = Serial.readStringUntil('\n');
      Serial.println(command);
    } while (Serial.available() > 0);
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
      int firstComma = command.indexOf(',');
      int secondComma = command.indexOf(',', firstComma + 1);
      int thirdComma = command.indexOf(',', secondComma + 1);
      
      long movement_x = command.substring(0, firstComma).toInt();
      long movement_y = command.substring(firstComma + 1, secondComma).toInt();
      long cam_x = command.substring(secondComma + 1, thirdComma).toInt();
      long cam_y = command.substring(thirdComma + 1).toInt();

      if (abs(stepperx.currentPosition() - cam_x) > 20) 
      {
      stepperx.setCurrentPosition(cam_x);
      }

      if (abs(steppery.currentPosition() - cam_y) > 20) 
      {
        steppery.setCurrentPosition(cam_y);
      }

      long positions[2] = { movement_x, movement_y };
      if (movement_x >= 0 && movement_x <= MAX_X && movement_y >= 0 && movement_y <= MAX_Y) {

        SetStepperSettings();
        // steppers.moveTo(positions); // For MulitStepper Libary


        // steppers.runSpeedToPosition();



        MoveToPosition(movement_x, movement_y);
        SetStepperSettings();
        if(stepperx.currentPosition()== 942 && steppery.currentPosition() == 101)
        {
          Serial.print("HomePosition");
        }
        else
        {
          Serial.print("OK");
        }
        //stepperx.runToNewPosition(movement_x);
        //steppery.runToNewPosition(movement_y);
        //Serial.println(millis() - StartZeit);
      }
    }
  }
}


void SetStepperProps(long movement_x, long movement_y) {
  // Calculate the distance each axis needs to move
  long distance_x = abs(movement_x - stepperx.currentPosition());
  long distance_y = abs(movement_y - steppery.currentPosition());
  // Serial.print("Distance for X axis: ");
  // Serial.println(distance_x);
  // Serial.print("Distance for Y axis: ");
  // Serial.println(distance_y);
  // Calculate the maximum distance to move
  long max_distance = max(distance_x, distance_y);
  // Calculate the ratio of distances to adjust acceleration
  float distance_ratio = (float)distance_x / (float)distance_y;

  // Initialize acceleration values
  float accel_x = MAX_ACCEL;
  float accel_y = MAX_ACCEL_Y;
  // Adjust acceleration based on the ratio
  if (distance_ratio > 1) {
    // X-axis needs more acceleration
    accel_y /= distance_ratio;
  } else {
    // Y-axis needs more acceleration
    accel_x *= distance_ratio;
  }
  //Serial.print("Setting acceleration for X axis: ");
  //Serial.println(accel_x);
  //Serial.print("Setting acceleration for Y axis: ");
  //Serial.println(accel_y);

  // Calculate the speed for each axis to reach the target at the same time
  int speed_x = sqrt(2 * distance_x * accel_x);
  int speed_y = sqrt(2 * distance_y * accel_y);


  //Serial.print("Setting speed for X axis: ");
  //Serial.println(speed_x);
  //Serial.print("Setting speed for Y axis: ");
  //Serial.println(speed_y);
  // Set the speed and acceleration for each axis
  stepperx.setMaxSpeed(speed_x);
  stepperx.setAcceleration(accel_x);
  steppery.setMaxSpeed(speed_y);
  steppery.setAcceleration(accel_y);
}

void MoveToPosition(long movement_x, long movement_y) {
  SetStepperProps(movement_x, movement_y);
  // Move both axes to their target positions simultaneously
  stepperx.moveTo(movement_x);
  steppery.moveTo(movement_y);
  // Keep running both motors until both have reached their target positions
  while (stepperx.isRunning() || steppery.isRunning()) {

    //Distance_to_position(movement_x, movement_y);

    stepperx.run();
    steppery.run();
  }
  // Reset the speed and acceleration to their default values
  SetStepperSettings();
  // Output the final positions
  //Serial.println("Final X position: " + String(stepperx.currentPosition()));
  //Serial.println("Final Y position: " + String(steppery.currentPosition()));
}

void Distance_to_position(long movement_x, long movement_y) {
  long distance_toPos_x = abs(movement_x - stepperx.currentPosition());
  long distance_toPos_y = abs(movement_y - steppery.currentPosition());


  Serial.print("Distance for X axis: ");
  Serial.print("Distance for Y axis: ");
  Serial.println(distance_toPos_x);
  Serial.println(distance_toPos_y);
}