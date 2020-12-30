#!/usr/bin/python3

#Importing dependencies
from smbus2 import SMBus, i2c_msg
import paho.mqtt.client as mqtt
import yaml
import os
import struct
import time

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
    for i in range(2):
        to_subscribe = topics_dict[topic_type]["plant"+str(i+1)]
        client.subscribe(to_subscribe)
        print("Beaglebon has subscribed to " + to_subscribe)

suscriber_function("get_params")
suscriber_function("on_off")
suscriber_function("update")

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
        if int(message.payload) == 0:
            print("Switching off plant 1")
            control_plant(plant1_addr,False)
        if int(message.payload) == 1:
            print("Switching on plant 1")
            control_plant(plant1_addr,True)
    if message.topic == topics_dict["on_off"]["plant2"]:
        if int(message.payload) == 0:
            print("Switching off plant 2")
            control_plant(plant2_addr,False)
        if int(message.payload) == 1:
            print("Switching on plant 2")
            control_plant(plant2_addr,True)
    if message.topic == topics_dict["update"]["plant1"]:
        control_plant(plant1_addr,True,message.payload.decode('utf-8'))
    if message.topic == topics_dict["update"]["plant2"]:
        control_plant(plant2_addr,True,message.payload.decode('utf-8'))
    
#Defining internal functions for the callback and for request data
def get_data(plant_address):
    #Requesting new data from tank control level sensors
    request = i2c_msg.write(plant_address,"d")
    msg = i2c_msg.read(plant_address,16)
    bus.i2c_rdwr(request,msg)
    msg_read = list(struct.unpack("<ffff",bytearray(list(msg))))

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
    msg_read = list(struct.unpack("<ffff",bytearray(list(msg))))
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
    request = list(bytes("o",'utf-8'))
    msg_on_off = i2c_msg.write(plant_address,request + list(bytes(on_off)))
    bus.i2c_rdwr(msg_on_off)
    if new_params != "":
    	new_params_list = list(map(float,new_params.split(";")))
    	if new_params_list[1] >= 0 and new_params_list[2] >= 0 and new_params_list[3] >= 0:
                #Requesting petition to update PID parameters
                request = list(bytes("u",'utf-8'))
                msg_pid = i2c_msg.write(plant_address,request + list(bytearray(struct.pack("<ffff",new_params_list[0],new_params_list[1],new_params_list[2],new_params_list[3]))))
                bus.i2c_rdwr(msg_pid)
                print("Updating parameters " + str(new_params_list))
    	if new_params_list[1] == -1 and new_params_list[2] == -1 and new_params_list[3] == -1:
                #Requesting petition to update PID parameters
                request = list(bytes("s",'utf-8'))
                msg_sp = i2c_msg.write(plant_address,request + list(bytearray(struct.pack("<f",new_params_list[0]))))
                bus.i2c_rdwr(msg_sp)
                print("Updating setpoint to  " + str(new_params_list[0]))


#Setting up the callback function to the client  
client.on_message = on_message

#Starting to listen from the broker
client.loop_start()

#Starting de loop to publish data
plant1_last_payload = ""
plant2_last_payload = ""

time.sleep(0.5)
while True:

    msg_plant1_payload = get_data(plant1_addr)
    if msg_plant1_payload != plant1_last_payload:
        msg_plant1_topic = topics_dict["data"]["plant1"]
        client.publish(msg_plant1_topic,msg_plant1_payload)
        plant1_last_payload = msg_plant1_payload
        time.sleep(1)        

    msg_plant2_payload = get_data(plant2_addr)
    if msg_plant2_payload != plant2_last_payload:
        msg_plant2_topic = topics_dict["data"]["plant2"]
        client.publish(msg_plant2_topic,msg_plant2_payload)
        plant2_last_payload = msg_plant2_payload
        time.sleep(1)
