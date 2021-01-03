#include "Wire.h"
const byte I2C_SLAVE_ADDR = 4;
byte par, msg;
int j;
float t, ti;
//Global Variables
float C1, C2, C3, i, i0, d, d0;
float Ts, Ti, Td, N;
float r, y, e, e0, kp, u;
float pv, cp;
bool on_off;
unsigned long timeNow, dataTime;

void setup() {

  TCCR2A = _BV(COM2A1) | _BV(WGM21) | _BV(WGM20); // Non-inverted, Fast PWM
  TCCR2B = _BV(CS20); //No prescaler

  pinMode(3, OUTPUT);
 
  //I2C bus configuration
  Wire.begin(I2C_SLAVE_ADDR);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);

  Serial.begin(115200);

  //Setting up variables
  Ts = 1;
  Ti = 8.14;
  Td = 1.02;
  N = 20;
  kp = 1;
  r = 15;     //SP
  
  timeNow = millis(); //Start counting up
  t=0;               //time since last value
    
  C1 = Ts/(2*Ti);
  C2 = 2*Td/(2*Td/N+Ts);
  C3 = (2*Td/N-Ts)/(2*Td/N+Ts);
   
  e0 = 0;
  i0 = 0;
  d0 = 0;

  cp=0;       //0% power pump
  on_off=1;   //Initialize pump on
}

// I2C bus interruptions routine
void receiveEvent(int bytes)
{
  if(Wire.available()){
    par = Wire.read();
      if(par=='u'){
        Serial.println("Updating variables:");
        for(j=0;j<sizeof(r);j++){
        ((byte*)&r)[j] = (byte)Wire.read();
        }
        for(j=0;j<sizeof(kp);j++){
          ((byte*)&kp)[j] = (byte)Wire.read();
        }
        for(j=0;j<sizeof(Ti);j++){
          ((byte*)&Ti)[j] = (byte)Wire.read();
        }
        for(j=0;j<sizeof(Td);j++){
          ((byte*)&Td)[j] = (byte)Wire.read();
        }
        Serial.print("SP: ");
        Serial.println(r);
        Serial.print("Kp: ");
        Serial.println(kp);
        Serial.print("Ti: ");
        Serial.println(Ti);
        Serial.print("Td: ");
        Serial.println(Td);
      }
      if(par=='s'){
        Serial.println("Updating setpoint:");
        for(j=0;j<sizeof(r);j++){
        ((byte*)&r)[j] = (byte)Wire.read();
        }
        Serial.print("SP: ");
        Serial.println(r);
      }
      if(par=='o'){
        on_off = !Wire.read();
        Serial.print("Switch to: ");
        Serial.println(on_off);
      }
      if(par=='d'){
        msg='d';
      }
      if(par=='p'){
        msg='p';
      }
  }
}

void requestEvent()
{
  Serial.println("Sending parameters ...");
  if(msg=='d'){
    Wire.write((byte*)&r, sizeof(r));
    Wire.write((byte*)&pv, sizeof(pv));   
    Wire.write((byte*)&cp, sizeof(cp));
    Wire.write((byte*)&t, sizeof(t));
  }
  if(msg=='p'){
    Wire.write((byte*)&r, sizeof(r));
    Wire.write((byte*)&kp, sizeof(kp));   
    Wire.write((byte*)&Ti, sizeof(Ti));
    Wire.write((byte*)&Td, sizeof(Td));
    Wire.write((byte*)&on_off, sizeof(on_off));
  }
}

void loop() {
  
  timeNow = millis();
  
  //Constants calculation
  C1 = Ts/(2*Ti);
  C2 = 2*Td/(2*Td/N+Ts);
  C3 = (2*Td/N-Ts)/(2*Td/N+Ts);

  //Calculating real variable: proporcional, integral and derivative
  y = map(analogRead(A0),0,1024,0,100); //Read of the tank level -> PV (Change scale: 0-5V -> 0-100%), Analog Input A0
  pv = y;             //Process value = tank level
  e = r-y;            //Error -> r=SP
  i = C1*(e+e0)+i0;     //Integral Value
  d = C2*(e-e0)+C3*d0;  //Derivativa Value
  u = kp*(e+i+d);     //Results power 0-100% equivalent to the Duty Cycle of the PWM sent to the plant -> CP
  cp = u;               //Control process -> power pump

  //Update previous values
  e0 = e;
  i0 = i;
  d0 = d;

  //Limitate cp output 0-100%
  //Control Process will be set to 0 if on_off = 0
  if(cp<0 || on_off == 0)
  {
    cp=0;
  }
  if(cp>100)
  {
    cp=100;
  }

  //Set the controll process to the power pump
  //PWM Output with Duty Cycle of u/cp (Control Process). Output Pin 3
  analogWrite(3,(cp/100)*255); 

  //Time Control Process
  dataTime = millis();   //Process time
  ti = (Ts*1000-(dataTime-timeNow))/1000;
  t = dataTime/1000;
  //Print main variables
  Serial.print("SP: ");
  Serial.println(r);
  Serial.print("PV: ");
  Serial.println(pv);
  Serial.print("CP: ");
  Serial.println(cp);
  Serial.print("Time: ");
  Serial.println(t);
  Serial.println("State: ");
  Serial.println(on_off);

  //Wait untill Ts
  delay(ti*1000);
}
