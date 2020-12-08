#Importing dependencies
from Adafruit_BBIO import GPIO
from smbus2 import SMBus,i2c_msg
import paho.mqtt.client as mqtt
import os

#Firstly, initialize de I2C pins for comunication
os.system("config-pin P9_17 i2c")
os.system("config-pin P9_18 i2c")

#Set addres for the controlled plants
plant1_addr = 80
plant2_addr = 81

#Setting up MQTT Connection
broker_address = ""
client = mqtt.Client("beaglebone")
client.connect(broker_address)
client.on_message = on_message

#Defining topics
data_topics = ("plant1/data","plant2/data")
params_topics = ("plant1/parameters","plant2/parameters")
get_params_topics = ("plant1/get_parameters","plant2/get_parameters")
on_off_topics = ("plant1/on_off","plant2/on_off")
update_topics = ("plant1/update_parameters","plant2/update_parameters")

#Subscribing and Publishing on respective topics
def suscriber_function(topic_list):
    for topic in topic_list:
        client.subscribe(topic)

suscriber_function(get_params_topics)
suscriber_function(on_off_topics)
suscriber_function(update_topics)

def publisher_function(topic_list, messages):
    for topic in topic_list:
        client.publish(topic, messages[topic_list.index(topic)])

publisher_function(data_topics, get_data)
publisher_function(params_topics, get_params)

#Defining callback function
def on_message(client, userdata, message):

    if message.topic == data_topics[0]:
        get_data(1)
    if message.topic == data_topics[1]:
        get_data(2)
    if message.topic == params_topics[0]:
        get_params(1)
    if message.topic == params_topics[0]:
        get_params(2)
    if message.topic == get_params_topics[0] and message.payload == "":
        get_params(1)
    if message.topic == get_params_topics[1] and message.payload == "":
        get_params(2)
    if message.topic == on_off_topics[0]:
        if message.payload == "0":
            control_plant(1,0)
        if message.payload == "1":
            control_plant(1,1)
    if message.topic == on_off_topics[1]:
        if message.payload == "0":
            control_plant(2,0)
        if message.payload == "1":
            control_plant(2,1)
    if message.topic == update_topics[0]:
        control_plant(1,1,message.payload)
    if message.topic == update_topics[1]:
        control_plant(2,1,message.payload)
    
#Defining internal functions for the callback
def get_data(plant_number):
    pass

def get_params(plant_number):
    pass

def control_plant(plant_number,on_off,new_params="50;1;8.14;1.02"):
    pass


    
    


