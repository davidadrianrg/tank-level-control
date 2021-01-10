#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Main Configuration: Update these lines with values suitable for your network.
#define ssid "WIFISSID"
#define pswd "WIFIPASS"
#define brokerIP "10.20.28.145"
#define brokerPort 1883
#define clientId "WEMOSD1R1"
#define mqtt_topic "mqtt"    // this is the [root topic]
#define dataTopic "plant5/data"
#define parametersTopic "plant5/parameters"
#define getParametersTopic "plant5/get_parameters"
#define onoffTopic "plant5/on_off"
#define updateTopic "plant5/update_parameters"
#define pwmPIN D3
#define levelSensorPin A0

int j;
float t, ti, sp;
//Global Variables
float C1, C2, C3, i, i0, d, d0;
float Ts, Ti, Td, N;
float r, y, e, e0, kp, u;
float pv, cp;
bool on_off;
unsigned long timeNow, dataTime;
char msg[50];

//Initilializing WiFi & MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  // Setting up the connection to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, pswd);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

//Defining callback function for the mqtt loop
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  char inmsg[length+1];
  for (int f = 0; f < length; f++) {
    inmsg[f] = (char)payload[f];
  }
  inmsg[length] = '\0';
  Serial.print((char*) topic);

  if (!strcmp(topic,getParametersTopic)) {
    if ((char)payload[0] == '0') {
      snprintf(msg, 50, "%f;%f;%f;%f;%i", r,kp,Ti,Td,on_off);
      client.publish(parametersTopic, msg);
    }
  }
  if (!strcmp(topic,onoffTopic)) {
    if ((char)payload[0] == '1') {
    on_off=1;
    }
    if ((char)payload[0] == '0'){
      on_off=0;
    }
  }
  if (!strcmp(topic,updateTopic)) {
    float kp_in,Ti_in,Td_in;
    sscanf(inmsg, "%f;%f;%f;%f" , &r, &kp_in, &Ti_in, &Td_in);
    if (kp_in >= 0 && Ti_in >= 0 && Td_in >= 0)
    {
      kp = kp_in;
      Ti = Ti_in;
      Td = Td_in;
    }
    
    Serial.println(inmsg);
  }
}

void reconnect() {
  // Loop until device is connected to the broker
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(clientId)) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish(mqtt_topic, "connected");
      // ... and resubscribe
      client.subscribe(getParametersTopic);
      client.subscribe(onoffTopic);
      client.subscribe(updateTopic);
      Serial.print("subscribed to : ");
      Serial.println(getParametersTopic);
      Serial.print("subscribed to : ");
      Serial.println(onoffTopic);
      Serial.print("subscribed to : ");
      Serial.println(updateTopic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.print(" wifi=");
      Serial.print(WiFi.status());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(brokerIP, 1883);
  client.setCallback(callback);

  pinMode(pwmPIN, OUTPUT);

  //Setting up variables
  Ts = 1;
  Ti = 8.14;
  Td = 1.02;
  N = 20;
  kp = 1;
  r = 60;     //SP
    
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
  //Confirm if is still connected to mqtt broker
  if (!client.connected()) {
    reconnect();
  }

  timeNow = millis();
  
  client.loop();
  
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
  if(cp<0 || on_off==0)
  {
    cp=0;
  }
  if(cp>100)
  {
    cp=100;
  }

  //Set the controll process value to the power pump
  //PWM Output with Duty Cycle of u/cp (Control Process)
  analogWrite(pwmPIN,(cp/100)*1023);

  //Control time process
  dataTime = millis();   //Process time
  ti = (Ts*1000-(dataTime-timeNow))/1000;
  t = dataTime/1000;

  //Print main variables
  Serial.println("\n");
  Serial.print("SP: ");
  Serial.println(r);
  Serial.print("PV: ");
  Serial.println(pv);
  Serial.print("CP: ");
  Serial.println(cp);
  Serial.print("Time: ");
  Serial.println(t);
  Serial.print("Kp: ");
  Serial.println(kp);
  Serial.print("Ti: ");
  Serial.println(Ti);
  Serial.print("Td: ");
  Serial.println(Td);
  Serial.print("on_off: ");
  Serial.println(on_off);

  //Parsing data for the mqtt payload
  snprintf(msg, 50, "%f;%f;%f;%f", r,pv,cp,t);
  //Publishing plant data to the broker
  client.publish(dataTopic, msg);

  //Wait untill Ts
  delay(abs(ti*1000));
  
}
