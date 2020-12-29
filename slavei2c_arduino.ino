#include "Wire.h"
 
const byte I2C_SLAVE_ADDR = 0x20;
 
void setup()
{
   Serial.begin(115200);
 
   Wire.begin(I2C_SLAVE_ADDR);
   Wire.onReceive(receiveEvent);
   Wire.onRequest(requestEvent);
}
 
float data = 0;
float response = 1.23;
bool recepcionTerminada=0;
bool transmisionTerminada=0;
 
void receiveEvent(int bytes)
{
   data = 0;
   uint8_t index = 0;
   while (Wire.available())
   {
      //Puntero (auxiliar) que apunta a la dirección de memoria de data casteada a 4 bytes
      byte* pointer = (byte*)&data;
      //Se guarda el valor en las posiciones = guardar byte a byte en cada posicion de memoria casteada de data
      *(pointer + index) = (byte)Wire.read();
      index++;
   }
   recepcionTerminada=1;
}
 
void requestEvent()
{
   Wire.write((byte*)&response, sizeof(response));
   transmisionTerminada=1;
}
 
 
void loop() {
 
   if (recepcionTerminada)
   {
      Serial.println(data);
      recepcionTerminada = 0;
   }
   if (transmisionTerminada)
   {
      Serial.println(response);
      transmisionTerminada = 0;
   }
   
}
