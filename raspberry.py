#!/usr/bin/python3

#Importing dependencies
import spidev
import paho.mqtt.client as mqtt
import yaml
import struct
import time
import sys

#Firstly, read the configuration.yaml document
with open("configuration.yaml", "r") as ymlfile:
    cfg = yaml.load(ymlfile,  Loader=yaml.FullLoader)

#Remember enable the spi pins in raspi-config
#Initialize spi_bus object
spi = spidev.SpiDev()
spi_max_speed_hz = cfg["spi"]["max_speed_hz"]
spi_mode = cfg["spi"]["mode"]

#Set chip enable for the controlled plants
plant3_ce = cfg["spi"]["plant3_ce"]
plant4_ce = cfg["spi"]["plant4_ce"]
spi_bus = cfg["spi"]["spibus"]

#Setting up MQTT Connection
try:
    client = mqtt.Client("raspberry")
    client.connect(cfg["mqtt"]["broker"],cfg["mqtt"]["port"])
    print("Connected to the mqtt broker")
except:
    print("Unable to connect with the mqtt broker")
    sys.exit(1)

#Storing topics into a dictionary
topics_dict = cfg["topics"]

#Subscribing on respective topics
def suscriber_function(topic_type):
    for i in range(2,4):
        to_subscribe = topics_dict[topic_type]["plant"+str(i+1)]
        client.subscribe(to_subscribe)
        print("Raspberry Pi has subscribed to " + to_subscribe)

suscriber_function("get_params")
suscriber_function("on_off")
suscriber_function("update")

#Defining callback function
def on_message(client, userdata, message):

    if message.topic == topics_dict["get_params"]["plant3"] and message.payload == "":
        message.payload = get_params(spi_bus,plant3_ce)
        message.topic = topics_dict["params"]["plant3"]
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["get_params"]["plant4"] and message.payload == "":
        message.payload = get_params(spi_bus,plant4_ce)
        message.topic = topics_dict["params"]["plant4"]
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["on_off"]["plant3"]:
        if int(message.payload) == 0:
            print("Switching off plant 3")
            control_plant(spi_bus,plant3_ce,False)
        if int(message.payload) == 1:
            print("Switching on plant 3")
            control_plant(spi_bus,plant3_ce,True)
    if message.topic == topics_dict["on_off"]["plant4"]:
        if int(message.payload) == 0:
            print("Switching off plant 4")
            control_plant(spi_bus,plant4_ce,False)
        if int(message.payload) == 1:
            print("Switching on plant 4")
            control_plant(spi_bus,plant4_ce,True)
    if message.topic == topics_dict["update"]["plant3"]:
        control_plant(spi_bus,plant3_ce,True,message.payload.decode('utf-8'))
    if message.topic == topics_dict["update"]["plant4"]:
        control_plant(spi_bus,plant4_ce,True,message.payload.decode('utf-8'))

#Defining internal functions for the callback and for request data
def get_data(bus,ce):
    #Requesting new data from tank control level sensors
    request = bytes("d", 'utf-8')
    spi.open(bus,ce)
    spi.max_speed_hz = spi_max_speed_hz
    spi.mode = spi_mode
    spi.writebytes(request)
    #This line clear the parameter from the slave register
    msg_read = spi.readbytes(1)
    #Start reading float data bytes
    msg_read = spi.readbytes(16)
    spi.close()
    msg_read = list(struct.unpack("<ffff",bytearray(msg_read)))

    #Parsing to string for the mqtt payload
    payload = str(msg_read[0])
    msg_read.pop(0)
    for msg_unit in msg_read:
        payload = payload + ";" + str(msg_unit)
    return payload

def get_params(bus,ce):
    #Requesting parameters from tank control level sensors
    request = bytes("p", 'utf-8')
    spi.open(bus,ce)
    spi.max_speed_hz = spi_max_speed_hz
    spi.mode = spi_mode
    spi.writebytes(request)
    #This line clear the parameter from the slave register
    msg_read = spi.readbytes(1)
    #Start reading float data bytes
    msg_read = spi.readbytes(17)
    spi.close()
    msg_read = list(struct.unpack("<ffffb",bytearray(list(msg_read))))

    #Parsing to string for the mqtt payload
    payload = str(msg_read[0])
    msg_read.pop(0)
    for msg_unit in msg_read:
        payload = payload + ";" + str(msg_unit)
    return payload

def control_plant(bus,ce,on_off,new_params=""):
    #Opening the bus to send values
    spi.open(bus,ce)
    spi.max_speed_hz = spi_max_speed_hz
    spi.mode = spi_mode
    #Requesting on/off petition for switching the plant
    if new_params == "":
        request = bytes("o", 'utf-8')
        spi.writebytes(request)
        msg_on_off = list(bytearray(struct.pack("<b",on_off)))
        spi.writebytes(msg_on_off)  
    else:
        new_params_list = list(map(float,new_params.split(";")))
        if new_params_list[1] >= 0 and new_params_list[2] >= 0 and new_params_list[3] >= 0:
            #Requesting petition to update PID parameters
            request = bytes("u", 'utf-8')
            spi.writebytes(request)
            msg_pid = list(bytearray(struct.pack("<ffff",new_params_list[0],new_params_list[1],new_params_list[2],new_params_list[3])))
            spi.writebytes(msg_pid)
            print("Updating parameters " + str(new_params_list))

        if new_params_list[1] == -1 and new_params_list[2] == -1 and new_params_list[3] == -1:
            #Requesting petition to update setpoint
            request = bytes("s",'utf-8')
            spi.writebytes(request)
            msg_sp = list(bytearray(struct.pack("<f",new_params_list[0])))
            spi.writebytes(msg_sp)
            print("Updating setpoint to  " + str(new_params_list[0]))

    #Closing bus connection
    spi.close()


#Setting up the callback function to the client  
client.on_message = on_message

#Starting to listen from the broker
client.loop_start()

#Starting de loop to publish data
plant3_last_payload = ""
plant4_last_payload = ""

time.sleep(0.5)
while True:

    msg_plant3_payload = get_data(spi_bus,plant3_ce)
    if msg_plant3_payload != plant3_last_payload:
        msg_plant3_topic = topics_dict["data"]["plant3"]
        client.publish(msg_plant3_topic,msg_plant3_payload)
        plant3_last_payload = msg_plant3_payload
        time.sleep(1)

    msg_plant4_payload = get_data(spi_bus,plant4_ce)
    if msg_plant4_payload != plant4_last_payload:
        msg_plant4_topic = topics_dict["data"]["plant4"]
        client.publish(msg_plant4_topic,msg_plant4_payload)
        plant4_last_payload = msg_plant4_payload
        time.sleep(1)