// Code using Robust Arduino Serial Protocol: https://github.com/araffin/arduino-robust-serial
/*#include <Arduino.h>
#include <Servo.h>
#include <Metro.h>
#include "order.h"
#include "slave.h"
#include "parameters.h"

void setup()
{
  // Init Serial
  Serial.begin(115200);

  // Init Motor
  pinMode(SPEED_LEFT, OUTPUT);
  pinMode(SPEED_RIGHT, OUTPUT);
  pinMode(DIRECTION_LEFT, OUTPUT);
  pinMode(DIRECTION_RIGHT, OUTPUT);

  // Stop the car
  stop();

  // Init Servo
  //servomotor.attach(SERVOMOTOR_PIN);
  // Order between 0 and 180
 // servomotor.write(INITIAL_THETA);

  // Wait until the arduino is connected to master
//   while(!is_connected)
//   {
//     write_order(HELLO);
//     wait_for_bytes(1, 1000);
//     get_messages_from_serial();
//   }

}

void loop()
{
  get_messages_from_serial();
  update_motors_orders();
//   if(measureDistance.check() == 1){
//     actualDistance = MeasureDistance();
//     actualDistance = min(actualDistance,127);
//     write_i8(actualDistance);
//     delay(100);
//   }
}

void stop()
{
  //analogWrite(MOTOR_PIN, 0);
  //digitalWrite(DIRECTION_PIN, LOW);
  analogWrite(SPEED_LEFT, 0);
  digitalWrite(DIRECTION_LEFT, LOW);
  analogWrite(SPEED_RIGHT, 0);
  digitalWrite(DIRECTION_RIGHT, LOW);
}

void get_messages_from_serial()
{
  message = Serial.read();

}*/
