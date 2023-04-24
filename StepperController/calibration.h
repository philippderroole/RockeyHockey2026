#ifndef CALIBRATION_H
#define CALIBRATION_H
extern AccelStepper stepperx;
extern AccelStepper steppery;
void calibrate_x() {
  long homing = -1;
  stepperx.enableOutputs();
  while (digitalRead(END_PIN_X)) {
    stepperx.moveTo(homing);
    homing--;
    delay(1);
    stepperx.run();
  }
  stepperx.stop();
  stepperx.setCurrentPosition(0);
  stepperx.setMaxSpeed(MAX_SPEED);
  stepperx.setSpeed(MAX_SPEED);
  stepperx.setAcceleration(MAX_ACCEL);
  stepperx.disableOutputs();
}
void calibrate_y() {
  long homing = -1;
  steppery.enableOutputs();
  while (digitalRead(END_PIN_Y)) {
    steppery.moveTo(homing);
    delay(1);
    homing--;
    steppery.run();
  }
  steppery.stop();
  steppery.setCurrentPosition(0);
  steppery.setMaxSpeed(MAX_SPEED);
  steppery.setSpeed(MAX_SPEED);
  steppery.setAcceleration(MAX_ACCEL);
  steppery.disableOutputs();
}
void calibrate(){
  calibrate_x();
  calibrate_y();
  Serial.println("ready");
}
#endif
