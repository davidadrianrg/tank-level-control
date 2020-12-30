#! /usr/bin/env python3
#  -*- coding: utf-8 -*-
#
# Main module implementing the client view for the GUI

import sys

import plotdata

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

import gui_tank_level_control_support


def vp_start_gui():
    '''Starting point when module is the main routine.'''
    global w, root
    root = tk.Tk()
    gui_tank_level_control_support.set_Tk_var()
    top = Control_Center (root)
    gui_tank_level_control_support.init(root, top)

w = None
def create_Control_Center(rt, *args, **kwargs):
    '''Starting point when module is imported by another module.
       Correct form of call: 'create_Control_Center(root, *args, **kwargs)' .'''
    global w, root
    #rt = root
    root = rt
    w = tk.Toplevel (root)
    gui_tank_level_control_support.set_Tk_var()
    top = Control_Center (w)
    gui_tank_level_control_support.init(w, top, *args, **kwargs)
    return (w, top)

class Control_Center:
    def __init__(self, top=None):
        '''This class configures and populates the toplevel window.
           top is the toplevel containing window.'''
        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9' # X11 color: 'gray85'
        _ana1color = '#d9d9d9' # X11 color: 'gray85'
        _ana2color = '#ececec' # Closest X11 color: 'gray92'
        self.style = ttk.Style()
        if sys.platform == "win32":
            self.style.theme_use('winnative')
        self.style.configure('.',background=_bgcolor)
        self.style.configure('.',foreground=_fgcolor)
        self.style.configure('.',font="TkDefaultFont")
        self.style.map('.',background=
            [('selected', _compcolor), ('active',_ana2color)])

        top.geometry("716x564+941+329")
        top.minsize(1, 1)
        top.maxsize(2545, 1410)
        top.resizable(1,  1)
        top.title("Control Center")

        self.style.map('Checkbutton',background=
            [('selected', _bgcolor), ('active', _ana2color)])
        self.Checkbutton_SP = tk.Checkbutton(top)
        self.Checkbutton_SP.place(relx=0.141, rely=0.757, relwidth=0.07
                , relheight=0.0, height=29)
        self.Checkbutton_SP.configure(variable=gui_tank_level_control_support.ch_sp)
        self.Checkbutton_SP.configure(takefocus="")
        self.Checkbutton_SP.configure(text='''SP''')
        self.Checkbutton_SP.configure(cursor="fleur")
        self.Checkbutton_SP.bind('<ButtonRelease-1>',lambda e:gui_tank_level_control_support.draw_sp(e))

        self.Plot = tk.Frame(top)
        self.Plot.place(relx=0.034, rely=0.021, relheight=0.691, relwidth=0.934)
        self.Plot.configure(borderwidth="2")
        self.Plot.configure(cursor="fleur")
        self.Plot.configure(relief="ridge")
        top.graph = plotdata.plotdata(self.Plot)

        self.Label_SP = tk.Label(top)
        self.Label_SP.place(relx=0.098, rely=0.778, height=5, width=25)
        self.Label_SP.configure(background="#000000")

        self.Checkbutton_PV = tk.Checkbutton(top)
        self.Checkbutton_PV.place(relx=0.141, rely=0.801, relwidth=0.073
                , relheight=0.0, height=29)
        self.Checkbutton_PV.configure(variable=gui_tank_level_control_support.ch_pv)
        self.Checkbutton_PV.configure(takefocus="")
        self.Checkbutton_PV.configure(text='''PV''')
        self.Checkbutton_PV.configure(cursor="fleur")
        self.Checkbutton_PV.bind('<ButtonRelease-1>',lambda e:gui_tank_level_control_support.draw_pv(e))

        self.Label_PV = tk.Label(top)
        self.Label_PV.place(relx=0.098, rely=0.823, height=5, width=25)
        self.Label_PV.configure(background="#0000ff")
        

        self.Label_Error = tk.Label(top)
        self.Label_Error.place(relx=0.098, rely=0.867, height=5, width=25)
        self.Label_Error.configure(background="#ff0000")

        self.Label_CP = tk.Label(top)
        self.Label_CP.place(relx=0.098, rely=0.91, height=5, width=25)
        self.Label_CP.configure(background="#038b28")

        self.Checkbutton_Error = tk.Checkbutton(top)
        self.Checkbutton_Error.place(relx=0.141, rely=0.846, relwidth=0.126
                , relheight=0.0, height=28)
        self.Checkbutton_Error.configure(variable=gui_tank_level_control_support.ch_error)
        self.Checkbutton_Error.configure(takefocus="")
        self.Checkbutton_Error.configure(text='''Error''')
        self.Checkbutton_Error.configure(cursor="fleur")
        self.Checkbutton_Error.bind('<ButtonRelease-1>',lambda e:gui_tank_level_control_support.draw_error(e))

        self.Checkbutton_CP = tk.Checkbutton(top)
        self.Checkbutton_CP.place(relx=0.141, rely=0.888, relwidth=0.068
                , relheight=0.0, height=29)
        self.Checkbutton_CP.configure(variable=gui_tank_level_control_support.ch_cp)
        self.Checkbutton_CP.configure(takefocus="")
        self.Checkbutton_CP.configure(text='''CP''')
        self.Checkbutton_CP.configure(cursor="fleur")
        self.Checkbutton_CP.bind('<ButtonRelease-1>',lambda e:gui_tank_level_control_support.draw_cp(e))

        self.TCombobox_Plant = ttk.Combobox(top,state="readonly")
        self.TCombobox_Plant.place(relx=0.332, rely=0.778, relheight=0.051
                , relwidth=0.229)
        self.TCombobox_Plant.configure(textvariable=gui_tank_level_control_support.combobox)
        self.TCombobox_Plant.configure(takefocus="")
        self.TCombobox_Plant.configure(cursor="fleur")
        self.TCombobox_Plant["values"] = ["Planta 1", "Planta 2", "Planta 3", "Planta 4", "Planta 5", "Planta 6"]
        self.TCombobox_Plant.set("Planta 1")
        self.TCombobox_Plant.bind('<<ComboboxSelected>>',lambda e:gui_tank_level_control_support.change_plant(e))

        self.TEntry_SP = ttk.Entry(top)
        self.TEntry_SP.place(relx=0.335, rely=0.869, relheight=0.041
                , relwidth=0.089)
        self.TEntry_SP.configure(textvariable=gui_tank_level_control_support.tentry_sp)
        self.TEntry_SP.configure(takefocus="")
        self.TEntry_SP.configure(cursor="fleur")

        self.Button_sp = tk.Button(top)
        self.Button_sp.place(relx=0.45, rely=0.867, height=23, width=71)
        self.Button_sp.configure(text='''SP''')
        self.Button_sp.bind('<Button-1>',lambda e:gui_tank_level_control_support.update_setpoint(e))

        self.TEntry_kp = ttk.Entry(top)
        self.TEntry_kp.place(relx=0.613, rely=0.77, relheight=0.041
                , relwidth=0.089)
        self.TEntry_kp.configure(textvariable=gui_tank_level_control_support.tentry_kp)
        self.TEntry_kp.configure(takefocus="")
        self.TEntry_kp.configure(cursor="fleur")

        self.Label_kp = tk.Label(top)
        self.Label_kp.place(relx=0.716, rely=0.755, height=29, width=45)
        self.Label_kp.configure(cursor="fleur")
        self.Label_kp.configure(text='''Kp''')

        self.TEntry_ti = ttk.Entry(top)
        self.TEntry_ti.place(relx=0.613, rely=0.835, relheight=0.041
                , relwidth=0.089)
        self.TEntry_ti.configure(textvariable=gui_tank_level_control_support.tentry_ti)
        self.TEntry_ti.configure(takefocus="")
        self.TEntry_ti.configure(cursor="xterm")

        self.TEntry_td = ttk.Entry(top)
        self.TEntry_td.place(relx=0.613, rely=0.899, relheight=0.035
                , relwidth=0.098)
        self.TEntry_td.configure(textvariable=gui_tank_level_control_support.tentry_td)
        self.TEntry_td.configure(takefocus="")
        self.TEntry_td.configure(cursor="fleur")

        self.Label_ti = tk.Label(top)
        self.Label_ti.place(relx=0.719, rely=0.823, height=29, width=44)
        self.Label_ti.configure(activebackground="#f9f9f9")
        self.Label_ti.configure(cursor="fleur")
        self.Label_ti.configure(text='''Ti''')

        self.Label_td = tk.Label(top)
        self.Label_td.place(relx=0.73, rely=0.888, height=29, width=35)
        self.Label_td.configure(activebackground="#f9f9f9")
        self.Label_td.configure(cursor="fleur")
        self.Label_td.configure(text='''Td''')

        self.Button_update = tk.Button(top)
        self.Button_update.place(relx=0.806, rely=0.759, height=33, width=101)
        self.Button_update.configure(cursor="fleur")
        self.Button_update.configure(text='''Update''')
        self.Button_update.bind('<Button-1>',lambda e:gui_tank_level_control_support.update_parameters(e))

        self.Button_on_off = tk.Button(top)
        self.Button_on_off.place(relx=0.8, rely=0.844, height=63, width=101)
        self.Button_on_off.configure(background="#11d82c")
        self.Button_on_off.configure(cursor="fleur")
        self.Button_on_off.configure(text='''ON''')
        self.Button_on_off.configure(textvariable=gui_tank_level_control_support.on_off_button)
        self.Button_on_off.bind('<Button-1>',lambda e:gui_tank_level_control_support.switch_plant(e))

if __name__ == '__main__':
    vp_start_gui()
