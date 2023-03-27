#include <Arduino.h>
#include <AccelStepper.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
/*
 * 11: Limit Z-Axis
 * 10: Limit Y-Axis
 * 9 : Limit X-Axis
 * 8 : Stepper Enable/Disable
 * 7 : Direction Z
 * 6 : Direction Y
 * 5 : Direction X
 * 4 : StepPulse Z
 * 3 : StepPulse Y
 * 2 : StepPulse X
 *
 * 1 Motor  : X
 * 2 Motoren: Y
 *
 * Y Positive = Bildschirme
 * Y Negative= Tafel
 *
 * X Postive = Tür
 * X Negative = Fenster
 */
#define ENABLE_PIN 8
#define MOTOR_X_STEP_PIN 2
#define MOTOR_X_DIR_PIN 5
#define MOTOR_Y_STEP_PIN 3
#define MOTOR_Y_DIR_PIN 6
#define END_PIN_X 9
#define END_PIN_Y 10

#define MAX_SPEED 9000
#define MAX_ACCELERATION 2500000000
#define MAX_X_POS 22800
#define MAX_Y_POS 15600
AccelStepper stepperx(1, MOTOR_X_STEP_PIN, MOTOR_X_DIR_PIN);
AccelStepper steppery(1, MOTOR_Y_STEP_PIN, MOTOR_Y_DIR_PIN);
enum Steppers{X,Y};

void SafeMoveTo(Steppers stepper , long absolute) {
  //check distance to endstops and direction to set speed -> avoid crash
  switch (stepper) {
    case X:  //X
    
      break;
    case Y:  // y
      break;
  }
}
void SafeMove(Steppers stepper, long relative){
 //check distance to endstops and direction to set speed -> avoid crash
}
void random_movement() {
  int lowerx = -20000;
  int lowery = -15000;
  int rand_x;
  int rand_y;
  do {
    rand_x = random(lowerx, MAX_X_POS);
    rand_x = (rand_x + 500) / 1000;
    rand_x = rand_x * 1000;
  } while (((rand_x + stepperx.currentPosition()) > MAX_X_POS) || ((rand_x + stepperx.currentPosition()) < 1000) || (rand_x == 0));
  do {
    rand_y = random(lowery, MAX_Y_POS);
    rand_y = (rand_y + 500) / 1000;
    rand_y = rand_y * 1000;
  } while (((rand_y + steppery.currentPosition()) > MAX_Y_POS) || ((rand_y + steppery.currentPosition()) < 1000) || (rand_y == 0));
  SafeMove(X,rand_x);
  SafeMove(Y,rand_y);
  //stepperx.move(rand_x);
  //steppery.move(rand_y);
}

//calibrates position by moving till end switch toggled
void calibrate_x() {
  long homing = -1;
  while (digitalRead(END_PIN_X)) {
    //stepperx.moveTo(homing);
    SafeMoveTo(X,homing);
    homing--;
    stepperx.run();
  }
  stepperx.setCurrentPosition(0);
  //stepperx.moveTo(11400);
  SafeMoveTo(X,11400);
  stepperx.run();
}

void calibrate_y() {
  long homing = -1;
  steppery.enableOutputs();
  stepperx.enableOutputs();
  while (digitalRead(END_PIN_Y)) {
   // steppery.moveTo(homing);
   SafeMoveTo(Y,homing);
    homing--;
    steppery.run();
  }
  steppery.setCurrentPosition(0);
  //steppery.moveTo(7800);
  SafeMoveTo(Y,7800);
  steppery.run();
}

void setup() {
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(END_PIN_X, INPUT_PULLUP);
  pinMode(END_PIN_Y, INPUT_PULLUP);
  stepperx.setPinsInverted(false, false, true);
  steppery.setPinsInverted(false, false, true);
  stepperx.setMaxSpeed(MAX_SPEED);
  stepperx.setAcceleration(MAX_ACCELERATION);
  stepperx.setSpeed(MAX_SPEED);
  steppery.setMaxSpeed(MAX_SPEED);
  steppery.setAcceleration(MAX_ACCELERATION);
  steppery.setSpeed(MAX_SPEED);
  stepperx.setEnablePin(ENABLE_PIN);
  steppery.setEnablePin(ENABLE_PIN);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    String movement_string = Serial.readStringUntil('\n');
    if ((movement_string == "ready\n") || (movement_string == "ready")) {
      Serial.print("moved");
    } else if ((movement_string == "calibrate\n") || (movement_string == "calibrate")) {
      calibrate_x();
      calibrate_y();
    } else {
      int delimiterIndex = movement_string.indexOf(',');
      String XValue = movement_string.substring(0, delimiterIndex);
      String YValue = movement_string.substring(delimiterIndex + 1);
      Serial.println("YValue" + YValue + ',' + "XValue" + XValue);
      long movement_x = XValue.toInt();
      long movement_y = YValue.toInt();
      //stepperx.moveTo(movement_x);
      SafeMoveTo(X,movement_x);
      //steppery.moveTo(movement_y);
      SafeMoveTo(Y,movement_y);
    }
  }
  steppery.run();
}
