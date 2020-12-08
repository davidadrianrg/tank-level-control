#Importing dependencies
from smbus2 import SMBus as bus,i2c_msg
import paho.mqtt.client as mqtt
import yaml
import os

#Firstly, read the configuration.yaml document
with open("configuration.yaml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

#Initialize de I2C pins for comunication
os.system("config-pin " + cfg["i2c"]["pinclk"] + " i2c")
os.system("config-pin " + cfg["i2c"]["pinsda"] + " i2c")

#Set addres for the controlled plants
plant1_addr = cfg["i2c"]["plant1_address"]
plant2_addr = cfg["i2c"]["plant2_address"]

#Setting up MQTT Connection
client = mqtt.Client("beaglebone")
client.connect(cfg["mqtt"]["broker"],cfg["mqtt"]["port"])
client.on_message = on_message

#Storing topics into a dictionary
topics_dict = cfg["topics"]

#Subscribing and Publishing on respective topics
def suscriber_function(topic_type):   
    for topic in topics_dict[topic_type].values():
        client.subscribe(topic)

suscriber_function("get_params")
suscriber_function("on_off")
suscriber_function("update_parameters")

#Starting to listen from the broker
client.loop_start

#Defining callback function
def on_message(client, userdata, message):

    if message.topic == topics_dict["data"]["plant1"]:
        message.payload = get_data(plant1_addr)
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["data"]["plant2"]:
        message.payload = get_data(plant2_addr)
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["params"]["plant1"]:
        message.payload = get_params(plant1_addr)
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["params"]["plant2"]:
        message.payload = get_params(plant2_addr)
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["get_params"]["plant1"] and message.payload == "":
        message.payload = get_params(plant1_addr)
        client.publish(message.topic,message.payload)

    if message.topic == topics_dict["get_params"]["plant2"] and message.payload == "":
        message.payload = get_params(plant2_addr)
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
    
#Defining internal functions for the callback
def get_data(plant_address):
    #Requesting new data from tank control level sensors
    request = i2c_msg.write(plant_address,"d")
    msg = i2c_msg.read(plant_address,16)
    bus.i2c_rdwr(msg,request)
    #Parsing to string for the mqtt payload
    msg_list = list(msg)
    payload = ""
    for msg_unit in msg_list:
        payload = payload + ";" + str(msg_unit)
    return payload

def get_params(plant_address):
    #Requesting new parameters from tank control level
    request = i2c_msg.write(plant_address,"p")
    msg = i2c_msg.read(plant_address,16)
    bus.i2c_rdwr(msg,request)
    #Parsing to string for the mqtt payload
    msg_list = list(msg)
    payload = ""
    for msg_unit in msg_list:
        payload = payload + ";" + str(msg_unit)
    return payload

def control_plant(plant_address,on_off,new_params=""):
    #Requesting on/off petition for tank level control
    request = i2c_msg.write(plant_address,"o")
    bus.i2c_rdwr(request)
    #Sending on/off value
    msg_on_off = i2c_msg.write(plant_address,on_off)
    bus.i2c_rdwr(msg_on_off)
    if new_params != "":
        #Requesting petition to update PID parameters
        request = i2c_msg.write(plant_address,"u")
        bus.i2c_rdwr(request)
        #Sending new PID values
        msg_pid = i2c_msg.write(plant_address,new_params)
        bus.i2c_rdwr(msg_pid)
    


    
    


