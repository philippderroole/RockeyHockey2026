int movement_x;
int movement_y;
int MAX_X = 2100;
int MAX_Y = 2100;
void setup() {
 Serial.begin(115200);
}

void loop() {
 if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if(strcmp(command.c_str(), "maximum") == 0){
      Serial.print(MAX_X);
      Serial.print(",");
      Serial.println(MAX_Y);
    }else if(strcmp(command.c_str(), "position") == 0) {
      Serial.print(100);
      Serial.print(",");
      Serial.println(50);
    } else if (strcmp(command.c_str(), "calibrate") == 0){
      movement_x = 0;
      movement_y = 0;

    }else if(strcmp(command.c_str(), "status") == 0) {
      Serial.println("busy");
    } else {
      int delimiterIndex = command.indexOf(',');
      movement_x = command.substring(0, delimiterIndex).toInt();
      movement_y = command.substring(delimiterIndex + 1).toInt();
    }
  }
}
