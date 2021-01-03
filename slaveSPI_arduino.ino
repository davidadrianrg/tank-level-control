#include <SPI.h>
byte par=0;
int j=0,k=0,l=0,m=0,n=0;
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
 
  //SPI bus configuration
  SPCR |= bit (SPE);
  SPCR |= _BV(SPIE);
  pinMode (MISO, OUTPUT);
  //Enable SPI bus interruptions
  SPI.attachInterrupt();

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
  on_off=1;   //Inicialize pump on
}

// SPI bus interruptions routine
ISR (SPI_STC_vect)
{
  byte c = SPDR;
  switch(par)
  {
    case 0:
      par=c;
      break;
    case 'u':
      if(j<sizeof(r))
      {
        ((byte*)&r)[j]=c;
        j++;
      }
      else if(k<sizeof(kp))
      {
        ((byte*)&kp)[k]=c;
        k++;
      }
      else if(l<sizeof(Ti))
      {
        ((byte*)&Ti)[l]=c;
        l++;
      }
      else if(m<sizeof(Td))
      {
        ((byte*)&Td)[m]=c;
        m++;
      }
      if(m>=sizeof(Td))
      {
        Serial.println("Updated new parameters:");
        Serial.print("SP: ");
        Serial.println(r);
        Serial.print("Kp: ");
        Serial.println(kp);
        Serial.print("Ti: ");
        Serial.println(Ti);
        Serial.print("Td: ");
        Serial.println(Td);
        Serial.println("");
        j=0;      
        k=0;
        l=0;
        m=0;
        par=0;
      }
      break;
    case 'd':
      if(j<sizeof(r))
      {
        SPDR=((byte*)&r)[j];
        j++;
      }
      else if(k<sizeof(pv))
      {
        SPDR=((byte*)&pv)[k];
        k++;
      }
      else if(l<sizeof(cp))
      {
        SPDR=((byte*)&cp)[l];
        l++;
      }
      else if(m<sizeof(t))
      {
        SPDR=((byte*)&t)[m];
        m++;
      }
      if(m>=sizeof(t))
      {
        j=0;      
        k=0;
        l=0;
        m=0;
        par=0;
      }
      break;
    case 'p':
      if(j<sizeof(r))
      {
        SPDR=((byte*)&r)[j];
        j++;
      }
      else if(k<sizeof(kp))
      {
        SPDR=((byte*)&kp)[k];
        k++;
      }
      else if(l<sizeof(Ti))
      {
        SPDR=((byte*)&Ti)[l];
        l++;
      }
      else if(m<sizeof(Td))
      {
        SPDR=((byte*)&Td)[m];
        m++;
      }
      else if(n<sizeof(on_off))
      {
        SPDR=on_off;
        n++;
      }
      if(n>=sizeof(on_off))
      {
        j=0;      
        k=0;
        l=0;
        m=0;
        n=0;
        par=0;
      }
      break;
    case 'o':
      on_off = (bool)SPDR;
      par=0;
      break;
    case 's':
      if(j<sizeof(r)){
        ((byte*)&r)[j] = c;
        j++;
      }
      if(j>=sizeof(r)){
        Serial.println("Updated new setpoint:");
        Serial.print("SP: ");
        Serial.println(r);
        Serial.println("");
        j=0;
        par=0;
      }
      break;
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
  cp = u;           //Control process -> power pump

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

  //Control time process
  dataTime = millis();   //Process time
  ti = (Ts*1000-(dataTime-timeNow))/1000;
  t = dataTime/1000;
  //Print main variables
  Serial.println("Plant data values:");
  Serial.print("SP: ");
  Serial.println(r);
  Serial.print("PV: ");
  Serial.println(pv);
  Serial.print("CP: ");
  Serial.println(cp);
  Serial.print("Time: ");
  Serial.println(t);
  Serial.print("State: ");
  Serial.println(on_off);
  Serial.println("");

  //Wait untill Ts
  delay(ti*1000);
}
