#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# Support module implementing server logic for the GUI

import sys
import plotdata
import paho.mqtt.client as mqtt
import yaml

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

#Firstly, define init function to create window
def init(top, gui, *args, **kwargs):
    global w, top_level, root
    w = gui
    top_level = top
    root = top
    top_level.protocol("WM_DELETE_WINDOW", destroy_window)
    root.mainloop()

#Read the configuration.yaml document
with open("../configuration.yaml", "r") as ymlfile:
    cfg = yaml.load(ymlfile,  Loader=yaml.FullLoader)


#Setting up MQTT Connection
try:
    client = mqtt.Client("gui")
    client.connect(cfg["mqtt"]["broker"],cfg["mqtt"]["port"])
    print("Control Center connected to the broker")
except:
    print("Unable to connect with MQTT Broker")

#Storing topics into a dictionary
topics_dict = cfg["topics"]

#Subscribing and Publishing on respective topics
def suscriber_function(topic_type):   
    for topic in topics_dict[topic_type].values():
        client.subscribe(topic)

suscriber_function("data")
suscriber_function("params")

#Defining callback function
def on_message(client, userdata, message):

    if message.topic == topics_dict["data"]["plant1"]:
        plant1_data = message.payload.decode("utf-8").split(";")
        print_data(plant1_data,"Plant 1")

    if message.topic == topics_dict["data"]["plant2"]:
        plant2_data = message.payload.decode("utf-8").split(";")
        print_data(plant2_data,"Plant 2")
    
    if message.topic == topics_dict["data"]["plant3"]:
        plant3_data = message.payload.decode("utf-8").split(";")
        print_data(plant3_data,"Plant 3")

    if message.topic == topics_dict["data"]["plant4"]:
        plant4_data = message.payload.decode("utf-8").split(";")
        print_data(plant4_data,"Plant 4")

    if message.topic == topics_dict["data"]["plant5"]:
        plant5_data = message.payload.decode("utf-8").split(";")
        print_data(plant5_data,"Plant 5")

    if message.topic == topics_dict["data"]["plant6"]:
        plant6_data = message.payload.decode("utf-8").split(";")
        print_data(plant6_data,"Plant 6")
    
    if message.topic == topics_dict["params"]["plant1"]:
        plant1_params = message.payload.decode("utf-8").split(";")
        show_params(plant1_params)

    if message.topic == topics_dict["params"]["plant2"]:
        plant2_params = message.payload.decode("utf-8").split(";")
        show_params(plant2_params)
    
    if message.topic == topics_dict["params"]["plant3"]:
        plant3_params = message.payload.decode("utf-8").split(";")
        show_params(plant3_params)

    if message.topic == topics_dict["params"]["plant4"]:
        plant4_params = message.payload.decode("utf-8").split(";")
        show_params(plant4_params)

    if message.topic == topics_dict["params"]["plant5"]:
        plant5_params = message.payload.decode("utf-8").split(";")
        show_params(plant5_params)

    if message.topic == topics_dict["params"]["plant6"]:
        plant6_params = message.payload.decode("utf-8").split(";")
        show_params(plant6_params)


#Defining internal functions for the callback
def print_data(data,selected_plant):
    #Processing the data received from the plant
    delta_t = float(data[3])
    error = float(data[0]) - float(data[1])
    new_points = [[delta_t,float(data[0])],[delta_t,float(data[1])],[delta_t,error],[delta_t,float(data[2])]]
    #Drawing the new data on the graph if the plant is selected on the combobox
    if w.TCombobox_Plant.get() == selected_plant:
        top_level.graph.addPoint(new_points)
    

def show_params(parameters):
    #Writing parameters in TEntrys
    tentry_sp.set(parameters[0])
    tentry_kp.set(parameters[1])
    tentry_ti.set(parameters[2])
    tentry_td.set(parameters[3])
    if int(parameters[4]) == 0:
        on_off_button.set("ON")
        w.Button_on_off.configure(background="#11d82c")
    elif int(parameters[4]) == 1:
        on_off_button.set("OFF")
        w.Button_on_off.configure(background="#ff0000")


#Setting up the callback function to the client  
client.on_message = on_message

#Starting to listen from the broker
client.loop_start()

#Requesting the parameters for the default plant (Plant 1)
client.publish(topics_dict["get_params"]["plant1"],"")

def set_Tk_var():
    global ch_sp
    ch_sp = tk.BooleanVar()
    ch_sp.set(True)
    global ch_pv
    ch_pv = tk.BooleanVar()
    ch_pv.set(True)
    global ch_error
    ch_error = tk.BooleanVar()
    ch_error.set(True)
    global ch_cp
    ch_cp = tk.BooleanVar()
    ch_cp.set(True)
    global combobox
    combobox = tk.StringVar()
    global tentry_sp
    tentry_sp = tk.StringVar()
    global tentry_kp
    tentry_kp = tk.StringVar()
    global tentry_ti
    tentry_ti = tk.StringVar()
    global tentry_td
    tentry_td = tk.StringVar()
    global on_off_button
    on_off_button = tk.StringVar()
    on_off_button.set('ON')

def change_plant(p1):
    top_level.graph.clear()
    plant_selected = w.TCombobox_Plant.get()
    plant_selected = plant_selected.split()

    #Requesting parameters for the new plant selected
    client.publish(topics_dict["get_params"]["plant"+plant_selected[1]],"")

    sys.stdout.flush()

def draw_cp(p1):
    top_level.graph.hide_show_line([ch_sp.get(), ch_pv.get(), ch_error.get(), ch_cp.get()])
    sys.stdout.flush()

def draw_error(p1):
    top_level.graph.hide_show_line([ch_sp.get(), ch_pv.get(), ch_error.get(), ch_cp.get()])
    sys.stdout.flush()

def draw_pv(p1):
    top_level.graph.hide_show_line([ch_sp.get(), ch_pv.get(), ch_error.get(), ch_cp.get()])
    sys.stdout.flush()

def draw_sp(p1):
    top_level.graph.hide_show_line([ch_sp.get(), ch_pv.get(), ch_error.get(), ch_cp.get()])
    sys.stdout.flush()

def switch_plant(p1):
    plant_selected = w.TCombobox_Plant.get().split()
    if on_off_button.get() == "OFF":
        on_off = 0
        client.publish(topics_dict["on_off"]["plant"+plant_selected[1]],on_off)
        on_off_button.set("ON")
        w.Button_on_off.configure(background="#11d82c")
        print("Switch off plant " + plant_selected[1])
    elif on_off_button.get() == "ON":
        on_off = 1
        client.publish(topics_dict["on_off"]["plant"+plant_selected[1]],on_off)
        on_off_button.set("OFF")
        w.Button_on_off.configure(background="#ff0000")
        print("Switch on plant " + plant_selected[1])
    sys.stdout.flush()

def update_parameters(p1):
    plant_selected = w.TCombobox_Plant.get().split()
    new_params = tentry_sp.get() + ";" + tentry_kp.get() + ";" + tentry_ti.get() + ";" + tentry_td.get()
    client.publish(topics_dict["update"]["plant"+plant_selected[1]],new_params)
    print("Loaded new parameters to plant " + plant_selected[1])
    sys.stdout.flush()

def update_setpoint(p1):
    plant_selected = w.TCombobox_Plant.get().split()
    new_sp = tentry_sp.get() + ";" + "-1" + ";" + "-1" + ";" + "-1"
    client.publish(topics_dict["update"]["plant"+plant_selected[1]],new_sp)
    print("Loaded new setpoint: " + tentry_sp.get() + " to plant " + plant_selected[1])
    sys.stdout.flush()

def destroy_window():
    # Function which closes the window.
    global root
    root.quit()
    root = None

if __name__ == '__main__':
    import gui_tank_level_control
    gui_tank_level_control.vp_start_gui()
    