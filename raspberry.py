#Importing dependencies
import spidev
import paho.mqtt.client as mqtt
import yaml
import struct

#Firstly, read the configuration.yaml document
with open("configuration.yaml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

#Remember enable the spi pins in raspi-config
#Initialize spi_bus object
spi = spidev.SpiDev()
spi.max_speed_hz = cfg["spi"]["max_speed_hz"]
spi.mode = cfg["spi"]["mode"]

#Set chip enable for the controlled plants
plant3_ce = cfg["spi"]["plant3_ce"]
plant4_ce = cfg["spi"]["plant4_ce"]
spi_bus = cfg["spi"]["spibus"]

#Setting up MQTT Connection
client = mqtt.Client("beaglebone")
client.connect(cfg["mqtt"]["broker"],cfg["mqtt"]["port"])

#Storing topics into a dictionary
topics_dict = cfg["topics"]

#Subscribing on respective topics
def suscriber_function(topic_type):   
    for i in range(2,4):
        client.subscribe(topics_dict[topic_type].values()[i])

suscriber_function("get_params")
suscriber_function("on_off")
suscriber_function("update_parameters")

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
        if message.payload == "0":
            control_plant(spi_bus,plant3_ce,0)
        if message.payload == "1":
            control_plant(spi_bus,plant3_ce,1)
    if message.topic == topics_dict["on_off"]["plant4"]:
        if message.payload == "0":
            control_plant(spi_bus,plant4_ce,0)
        if message.payload == "1":
            control_plant(spi_bus,plant4_ce,1)
    if message.topic == topics_dict["update"]["plant3"]:
        control_plant(spi_bus,plant3_ce,1,message.payload)
    if message.topic == topics_dict["update"]["plant4"]:
        control_plant(spi_bus,plant4_ce,1,message.payload)

#Defining internal functions for the callback and for request data
def get_data(bus,ce):
    #Requesting new data from tank control level sensors
    request = bytes("d", 'utf-8')
    request_bytes = list(bytearray(struct.pack("c",request)))
    spi.open(bus,ce)
    spi.writebytes(request_bytes)
    msg_read = spi.readbytes(16)
    spi.close()
    msg_read = struct.unpack("<ffff",bytearray(msg_read))

    #Parsing to string for the mqtt payload
    payload = str(msg_read[0])
    msg_read.pop(0)
    for msg_unit in msg_read:
        payload = payload + ";" + str(msg_unit)
    return payload

def get_params(bus,ce):
    #Requesting parameters from tank control level sensors
    request = bytes("p", 'utf-8')
    request_bytes = list(bytearray(struct.pack("c",request)))
    spi.open(bus,ce)
    spi.writebytes(request_bytes)
    msg_read = spi.readbytes(16)
    on_off = spi.readbytes(2)
    spi.close()
    msg_read = struct.unpack("<ffff",bytearray(list(msg_read)))
    on_off = struct.unpack("<i",bytearray(list(on_off)))

    #Parsing to string for the mqtt payload
    payload = str(msg_read[0])
    msg_read.pop(0)
    for msg_unit in msg_read:
        payload = payload + ";" + str(msg_unit)
    payload = payload + ";" + str(on_off)
    return payload

def control_plant(bus,ce,on_off,new_params=""):
    #Requesting on/off petition for switching the plant
    request = bytes("o", 'utf-8')
    request_bytes = list(bytearray(struct.pack("c",request)))
    spi.open(bus,ce)
    spi.writebytes(request_bytes)
    spi.writebytes(on_off)
    
    if new_params != "":
        #Requesting petition to update PID parameters
        request = bytes("u", 'utf-8')
        request_bytes = list(bytearray(struct.pack("c",request)))
        spi.writebytes(request_bytes)
        new_params = new_params.split(";")
        msg_pid = list(bytearray(struct.pack("s",new_params)))
        spi.writebytes(msg_pid)
    
    #Closing bus connection
    spi.close()


#Setting up the callback function to the client  
client.on_message = on_message

#Starting to listen from the broker
client.loop_start()

#Starting de loop to publish data
plant3_last_payload = ""
plant4_last_payload = ""

while True:

    msg_plant3_payload = get_data(spi_bus,plant3_ce)
    if msg_plant3_payload != plant3_last_payload:
        msg_plant3_topic = topics_dict["data"]["plant3"]
        client.publish(msg_plant3_topic,msg_plant3_payload)
        plant3_last_payload = msg_plant3_payload

    msg_plant4_payload = get_data(spi_bus,plant4_ce)
    if msg_plant4_payload != plant4_last_payload:
        msg_plant4_topic = topics_dict["data"]["plant4"]
        client.publish(msg_plant4_topic,msg_plant4_payload)
        plant4_last_payload = msg_plant4_payload