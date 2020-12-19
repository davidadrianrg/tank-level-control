#Importing dependencies
from smbus2 import SMBus, i2c_msg
import paho.mqtt.client as mqtt
import yaml
import os
import struct

#Firstly, read the configuration.yaml document
with open("configuration.yaml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

#Initialize de I2C pins for comunication
os.system("config-pin " + cfg["i2c"]["pinclk"] + " i2c")
os.system("config-pin " + cfg["i2c"]["pinsda"] + " i2c")
#Initialize bus object
bus = SMBus(cfg["i2c"]["i2cbus"])

#Set addres for the controlled plants
plant1_addr = cfg["i2c"]["plant1_address"]
plant2_addr = cfg["i2c"]["plant2_address"]

#Setting up MQTT Connection
client = mqtt.Client("beaglebone")
client.connect(cfg["mqtt"]["broker"],cfg["mqtt"]["port"])

#Storing topics into a dictionary
topics_dict = cfg["topics"]

#Subscribing on respective topics
def suscriber_function(topic_type):   
    for topic in topics_dict[topic_type].values():
        client.subscribe(topic)

suscriber_function("get_params")
suscriber_function("on_off")
suscriber_function("update_parameters")

#Defining callback function
def on_message(client, userdata, message):

    if message.topic == topics_dict["get_params"]["plant1"] and message.payload == "":
        message.payload = get_params(plant1_addr)
        message.topic = topics_dict["params"]["plant1"]
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["get_params"]["plant2"] and message.payload == "":
        message.payload = get_params(plant2_addr)
        message.topic = topics_dict["params"]["plant2"]
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["on_off"]["plant1"]:
        if message.payload == "0":
            control_plant(plant1_addr,0)
        if message.payload == "1":
            control_plant(plant1_addr,1)
    if message.topic == topics_dict["on_off"]["plant2"]:
        if message.payload == "0":
            control_plant(plant2_addr,0)
        if message.payload == "1":
            control_plant(plant2_addr,1)
    if message.topic == topics_dict["update"]["plant1"]:
        control_plant(plant1_addr,1,message.payload)
    if message.topic == topics_dict["update"]["plant2"]:
        control_plant(plant2_addr,1,message.payload)
    
#Defining internal functions for the callback and for request data
def get_data(plant_address):
    #Requesting new data from tank control level sensors
    request = i2c_msg.write(plant_address,"d")
    msg = i2c_msg.read(plant_address,16)
    bus.i2c_rdwr(request,msg)
    msg_read = struct.unpack("<ffff",bytearray(list(msg)))

    #Parsing to string for the mqtt payload
    payload = str(msg_read[0])
    msg_read.pop(0)
    for msg_unit in msg_read:
        payload = payload + ";" + str(msg_unit)
    return payload

def get_params(plant_address):
    #Requesting parameters from tank control level sensors
    request = i2c_msg.write(plant_address,"p")
    msg = i2c_msg.read(plant_address,16)
    on_off_state = i2c_msg.read(plant_address,2)
    bus.i2c_rdwr(request,msg,on_off_state)
    msg_read = struct.unpack("<ffff",bytearray(list(msg)))
    on_off = struct.unpack("<i",bytearray(list(on_off_state)))

    #Parsing to string for the mqtt payload
    payload = str(msg_read[0])
    msg_read.pop(0)
    for msg_unit in msg_read:
        payload = payload + ";" + str(msg_unit)
    payload = payload + ";" + str(on_off)
    return payload

def control_plant(plant_address,on_off,new_params=""):
    #Requesting on/off petition for switching the plant
    request = i2c_msg.write(plant_address,"o")
    msg_on_off = i2c_msg.write(plant_address,on_off)
    bus.i2c_rdwr(request,msg_on_off)

    if new_params != "":
        #Requesting petition to update PID parameters
        request = i2c_msg.write(plant_address,"u")
        new_params = new_params.split(";")
        msg_pid = i2c_msg.write(plant_address,new_params)
        bus.i2c_rdwr(request,msg_pid)

#Setting up the callback function to the client  
client.on_message = on_message

#Starting to listen from the broker
client.loop_start()

#Starting de loop to publish data
plant1_last_payload = ""
plant2_last_payload = ""

while True:

    msg_plant1_payload = get_data(plant1_addr)
    if msg_plant1_payload != plant1_last_payload:
        msg_plant1_topic = topics_dict["data"]["plant1"]
        client.publish(msg_plant1_topic,msg_plant1_payload)
        plant1_last_payload = msg_plant1_payload

    msg_plant2_payload = get_data(plant2_addr)
    if msg_plant2_payload != plant2_last_payload:
        msg_plant2_topic = topics_dict["data"]["plant2"]
        client.publish(msg_plant2_topic,msg_plant2_payload)
        plant2_last_payload = msg_plant2_payload


      
    


    
    


