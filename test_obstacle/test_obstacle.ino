#include <Servo.h>
#include <Metro.h>
Metro measureDistance = Metro(50);
Metro sweepServo = Metro(20);

unsigned long actualDistance = 0;

Servo myservo;  // create servo object to control a servo
int pos = 60;
int sweepFlag = 1;


int URPWM = 11; // PWM Output 0－25000US，Every 50US represent 1cm
int URTRIG= 10; // PWM trigger pin
uint8_t EnPwmCmd[4]={0x44,0x02,0xbb,0x01};    // distance measure command

void setup(){                                 // Serial initialization
  myservo.attach(9);
  Serial.begin(9600);                         // Sets the baud rate to 9600
  SensorSetup();
}

void loop(){
 if(measureDistance.check() == 1){
      actualDistance = MeasureDistance();
      Serial.println(actualDistance);
      delay(100);
 }

 if(sweepServo.check() == 1){
      servoSweep();
 }

}

void SensorSetup(){
  pinMode(URTRIG,OUTPUT);                     // A low pull on pin COMP/TRIG
  digitalWrite(URTRIG,HIGH);                  // Set to HIGH
  pinMode(URPWM, INPUT);                      // Sending Enable PWM mode command
  for(int i=0;i<4;i++){
      Serial.write(EnPwmCmd[i]);
   }
}

int MeasureDistance(){        // a low pull on pin COMP/TRIG  triggering a sensor reading
    digitalWrite(URTRIG, LOW);
    digitalWrite(URTRIG, HIGH);               // reading Pin PWM will output pulses
    unsigned long distance=pulseIn(URPWM,LOW);
    if(distance==50000){              // the reading is invalid.
      Serial.print("Invalid");
    }else{
      distance=distance/50;           // every 50us low level stands for 1cm
    }
    return distance;
}

void servoSweep(){
  if(sweepFlag ){
     if(pos>=30 && pos<=90){
        pos=pos+1;                                  // in steps of 1 degree
        myservo.write(pos);                         // tell servo to go to position in variable 'pos'
    }
      if(pos>89)  sweepFlag = false;                       // assign the variable again
  }else {
      if(pos>=30 && pos<=90){
        pos=pos-1;
        myservo.write(pos);
      }
      if(pos<31)  sweepFlag = true;
   }
}
