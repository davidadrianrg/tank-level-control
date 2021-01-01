#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <stdio.h>

#define wifiSSID "WIFISSID"
#define wifiPass "KEYPASS"
#define brokerIP "192.168.43.147"
#define brokerPort 1883
#define dataTopic "plant5/data"
#define parametersTopic "plant5/parameters"
#define getParametersTopic "plant5/get_parameters"
#define onoffTopic "plant5/on_off"
#define updateTopic "plant5/update_parameter"
#define pwmPIN 3
#define levelSensorPin A0

float t, ti, sp;
//Global Variables
float C1, C2, C3, i, i0, d, d0;
float Ts, Ti, Td, N;
float r, y, e, e0, kp, u;
float pv, cp;
int on_off;
unsigned long timeNow, dataTime;
char get_params;

//Initilializing WiFi & MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi(){
  delay(10);
  WiFi.begin(wifiSSID, wifiPass);
  Serial.print("Connecting WiFi ");
  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void callback(char* topic, byte* payload, unsigned int length){
  //Processing the payload
  char inmsg[length + 1];
  for (int j = 0; j < length; j++){
    inmsg[j] = (char)payload[j];
  }
  if(topic == getParametersTopic){
    inmsg[length] = '\0';
    sscanf(inmsg, "%c", &get_params);
  }
  if(topic == onoffTopic){
    inmsg[length] = '\0';
    sscanf(inmsg, "%i", &on_off);
  }
  if(topic == updateTopic){
    float sp_received, kp_received, ti_received, td_received;
    inmsg[length] = '\0';
    sscanf(inmsg, "%f;%f;%f;%f", &sp_received, &kp_received, &ti_received, &td_received);
    if(sp_received >= 0 && kp_received >= 0 && ti_received >= 0 && td_received >= 0){
      r = sp_received;
      kp = kp_received;
      Ti = ti_received;
      Td = td_received;
    }
  }
}

void setup() {

  pinMode(pwmPIN, OUTPUT);
 
  Serial.begin(115200);

  //Setting up MQTT connection
  setup_wifi();
  client.setServer(brokerIP, brokerPort);
  client.setCallback(callback);
  client.subscribe(getParametersTopic);
  client.subscribe(onoffTopic);
  client.subscribe(updateTopic);
  client.loop();
  Serial.println("Connected to the broker");

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

void loop() {
  
  timeNow = millis();
  
  //Constants calculation
  C1 = Ts/(2*Ti);
  C2 = 2*Td/(2*Td/N+Ts);
  C3 = (2*Td/N-Ts)/(2*Td/N+Ts);

  //Calculating real variable: proporcional, integral and derivative
  y = map(analogRead(levelSensorPin),0,1024,0,100); //Read of the tank level -> PV (Change scale: 0-3.3V -> 0-100%), Analog Input Pin
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
  if(cp<0 || on_off == 0)
  {
    cp=0;
  }
  if(cp>100)
  {
    cp=100;
  }

  //Set the controll process to the power pump
  //PWM Output with Duty Cycle of u/cp (Control Process).
  analogWrite(pwmPIN,(cp/100)*255);

  //Time Control Processs
  dataTime = millis();   //Process time
  ti = (Ts*1000-(dataTime-timeNow))/1000;
  t = dataTime/1000;

  //Publish new data values
  char* msg;
  snprintf(msg, 50,"%f;%f;%f;%f",r,pv,cp,t);
  client.publish(dataTopic, msg);

  //Print main variables
  Serial.print("SP: ");
  Serial.println(r);
  Serial.print("PV: ");
  Serial.println(pv);
  Serial.print("CP: ");
  Serial.println(cp);
  Serial.print("Time: ");
  Serial.println(t);

  //Publish parameters to the plant
  if(get_params == '\0'){
    char* msg;
    snprintf(msg, 50,"%f;%f;%f;%f;%i",r,kp,Ti,Td,on_off);
    client.publish(parametersTopic, msg);
    get_params = NAN;
  }

  //Wait untill Ts
  delay(ti*1000);
}
