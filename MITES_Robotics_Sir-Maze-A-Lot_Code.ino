int ena = 5, in1 = 4, in2 = 6, in3 = 7, in4 = 8, enb = 9;
const int trigPin = 10;
const int echoPin = 11;
long duration;
float cm, inches;
int stage = 1;
int turnCount = 0;
const int turnLimit = 6;
const int buttonPin = 12;  // the number of the pushbutton pin
const long debounceDelay = 50;
int buttonState = 1;   // variable for reading the pushbutton status
int lastButtonState = 1;     // previous state
bool running = false;
long lastDebounceTime = 0;
bool stopped = true;
int reading = 1;

void setup() {
  delay(1000);
  pinMode(ena, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  pinMode(enb, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  Serial.begin(9600);
  analogWrite(ena,147);
  analogWrite(enb,131);
  digitalWrite(in1,LOW);
  digitalWrite(in2,LOW);
  digitalWrite(in3,LOW);
  digitalWrite(in4,LOW);
}
void loop() {
  reading = digitalRead(buttonPin); // read the current state of the button
  // Check if the button state has changed from unpressed (HIGH) to pressed (LOW)  
  if(reading != lastButtonState){
    lastDebounceTime = millis();
  }
  if((millis() - lastDebounceTime) > debounceDelay){
    if(reading != buttonState){
      buttonState = reading;
      if(buttonState == 0){
        running = !running;
      }
    }
  }
  lastButtonState = reading;

  /*Serial.print("Button State: ");
  Serial.println(buttonState);
  Serial.print("Running: ");
  Serial.println(running);
  Serial.print("Reading: ");
  Serial.println(reading);
  Serial.print("Last Button State: ");
  Serial.println(lastButtonState);*/

  if(running == true){
    if(stopped == true){
      delay(3000);
    }
    stopped = false;
    Serial.println("Running mode active");

    // Clears the trigPin
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    // Sets the trigPin on HIGH state for 10 micro seconds
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    // Reads the echoPin, returns the sound wave travel time in microseconds
    duration = pulseIn(echoPin, HIGH);
    // Calculating the distance
    cm = (duration/2) / 29.1;     // Divide by 29.1 or multiply by 0.0343
    inches = cm / 2.54;   // Divide by 74 or multiply by 0.0135
    // Prints the distance on the Serial Monitor
    Serial.print(inches);
    Serial.print("in, ");
    Serial.print(cm);
    Serial.print("cm");
    Serial.println();

    if (inches <= 9) {
      digitalWrite(LED_BUILTIN, HIGH);

      if (stage == 1) {
        turnLeft();
        delay(320);
        stop();
        delay(100);
        stage = 2;  // switch to scanning mode
        turnCount = 0;
      }

      else if (stage == 2) {
        turnRight();
        delay(250);
        stop();
        delay(50);
        // Don’t re-read sensor here

        turnCount = turnCount + 1;
        if(turnCount >= turnLimit){
          stage = 3;
        }
      }

      else if(stage == 3) {
        endDance();
      }
    }

    else {
      // If distance is now safe, reset to stage 1
      stage = 1;
      digitalWrite(LED_BUILTIN, LOW);
      driveForward();
    }

    delay(100);
  }
  else{
    if (!stopped) {
      stop(); // Stop the robot only once
      digitalWrite(LED_BUILTIN, LOW); // Optional: indicate idle
      stopped = true;
    }
    delay(10); // Always wait a bit to stay safe and clean
  }
}
void turnReverse(){
  digitalWrite(in1,LOW);
  digitalWrite(in2,HIGH);
  digitalWrite(in3,LOW);
  digitalWrite(in4,HIGH);
  delay(597);
}
void driveForward(){
  digitalWrite(in1,LOW);
  digitalWrite(in2,HIGH);
  digitalWrite(in3,LOW);
  digitalWrite(in4,HIGH);
}
void stop(){
  digitalWrite(in1,LOW);
  digitalWrite(in2,LOW);
  digitalWrite(in3,LOW);
  digitalWrite(in4,LOW);
}
void turnRight(){
  digitalWrite(in1,HIGH);
  digitalWrite(in2,LOW);
  digitalWrite(in3,LOW);
  digitalWrite(in4,HIGH);
}
void turnLeft(){
  digitalWrite(in1,LOW);
  digitalWrite(in2,HIGH);
  digitalWrite(in3,HIGH);
  digitalWrite(in4,LOW);
}
void endDance(){
  for(int i = 0; i < 3; i++){
    digitalWrite(LED_BUILTIN, HIGH);
    turnRight();
    delay(200);
    digitalWrite(LED_BUILTIN, LOW);
    turnLeft();
    delay(200);    
  }
  stop();
  running = false;
}