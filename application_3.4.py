#! The imports
#!-------------
#!
#! The MPLFigureEditor is imported from current folder.
import os
import sys
os.environ["TRAITSUI_TOOLKIT"] = "wx"
from traits.trait_base import ETSConfig
ETSConfig.toolkit = "wx"

from threading import Thread
import threading
from time import sleep
from traits.api import *
from traitsui.api import View, Item, Group, Include, HSplit, Handler, VGroup
from traitsui.menu import NoButtons
from matplotlib.figure import Figure
import wx
from scipy import *
from mpl_figure_editor import MPLFigureEditor
import pyvisa
rm = pyvisa.ResourceManager()
import math
import numpy as np
from time import ctime, time
import os, datetime
from instruments2 import ls370, GS200, Picoscope
import warnings


#! User interface objects
#!------------------------
#!
#! These objects store information for the program to interact with the
#! user via traitsUI.

class Experiment(HasTraits):
    """ Object that contains the parameters that control the experiment, 
        modified by the user.
    """
    width = Float(30, label="Width", desc="width of the cloud")
    x = Float(50, label="X", desc="X position of the center")
    y = Float(50, label="Y", desc="Y position of the center")

class Results(HasTraits):
    """ Object used to display the results.
    """
    width = Float(30, label="Width", desc="width of the cloud") 
    x = Float(50, label="X", desc="X position of the center")
    y = Float(50, label="Y", desc="Y position of the center")

    view = View( Item('width', style='readonly'),
                 Item('x', style='readonly'),
                 Item('y', style='readonly'),
               )


class CurrentControl(HasTraits):
    """ Class that holds objecs to control the current
    """
    
    #TODO: Time before applying current, time with current on, time with current off, list off currents
    tBefore = Float(0.1, label="Time before applying current [min]")
    tOn = Float(5, label="Time with current on [min]")
    tOff = Float(10, label="Time with current off [min]")
    currents = String("0,1E-7,2E-7,3E-7,4E-7,5E-7,6E-7,7E-7", label="List of currents applied", desc="List of all currents to be applied, in order, seperated with comma (\',\'), no whitespace")
    apply_curr = Bool(False, label="Enable applying current", desc="WARNING: Don't use this mode together with \"slow scans only\"")
    CS = None
    VS = None
    
    view = View(Group(Group(
                Item('apply_curr'),
                Group(
                Item('tBefore'),
                Item('tOn'),
                Item('tOff'),
                Item('currents', springy=False, resizable=True), enabled_when='apply_curr')), show_border = True)
                )
    trait_view_elements_changed = False
    
    def add_dynamic_trait(self, name, trait):
        self.add_trait(name, trait)

    def initialize(self):
        if self.apply_curr:
            try:
                if not self.CS:
                    self.CS=GS200()
                sleep(1)
                try:
                    self.CS.SetMode("CURR")
                    sleep(1)
                    self.CS.SetCurrentRange(1E-3)
                except:
                    pass
            except Exception as e:
                print(f"Error while connecting to GS200: {e}")
            try:
                if not self.VS:
                    self.VS=Picoscope()
                sleep(1)
                self.VS.MeasParam('A')
                self.VS.MeasParam('B',en=False)
                self.VS.MeasParam('C',en=False)
                self.VS.MeasParam('D',en=False)
            except:
                print("Error while connecting to Picoscope")
            
            #turn the input string into a list of currents
            self.curr_list = self.currents.split(',')
            self.curr_list = [float(x) for x in self.curr_list]
            print(self.curr_list)
            
            #convert the input to seconds
            self.tBefore_s = self.tBefore*60
            self.tOn_s = self.tOn*60
            self.tOff_s = self.tOff*60
        else:
            print("Current control is disabled")

class Bridge(HasTraits):
    """ ls370 bridge objects. Implements both the ls370 parameters controls, and
        the data acquisition.
    """
    
    #initialize the ls370 bridge
    # MS = ls370()
    
    ResRangeList={'1 - 2 mOhm':         '1',
                  '2 - 6.32 mOhm':      '2',
                  '3 - 20 mOhm':        '3',
                  '4 - 63.2 mOhm':      '4',
                  '5 - 200 mOhm':       '5',
                  '6 - 632 mOhm':       '6',
                  '7 - 2 Ohm':          '7',
                  '8 - 6.32 Ohm':       '8',
                  '9 - 20 Ohm':         '9',
                  '10 - 63.2 Ohm':      '10',
                  '11 - 200 Ohm':       '11',
                  '12 - 632 Ohm':       '12',
                  '13 - 2 kOhm':        '13',
                  '14 - 6.32 kOhm':     '14',
                  '15 - 20 kOhm':       '15',
                  '16 - 63.2 kOhm':     '16',
                  '17 - 200 kOhm':      '17',
                  '18 - 632 kOhm':      '18',
                  '19 - 2 MOhm':        '19',
                  '20 - 6.32 MOhm':     '20',
                  '21 - 20 MOhm':       '21',
                  '22 - 63.2 MOhm':     '22',}
                        
    ExcitRangeList={'1 - 1.00 pA':        '1',
                        '2 - 3.16 pA':    '2',
                        '3 - 10 pA':      '3',
                        '4 - 31.6 pA':    '4',
                        '5 - 100 pA':     '5',
                        '6 - 316 pA':     '6',
                        '7 - 1.00 nA':    '7',
                        '8 - 3.16 nA':    '8',
                        '9 - 10 nA':      '9',
                        '10 - 31.6 nA':   '10',
                        '11 - 100 nA':    '11',
                        '12 - 316 nA':    '12',
                        '13 - 1.00 uA':   '13',
                        '14 - 3.16 uA':   '14',
                        '15 - 10 uA':     '15',
                        '16 - 31.6 uA':   '16',
                        '17 - 100 uA':    '17',
                        '18 - 316 uA':    '18',
                        '19 - 1 mA':      '19',
                        '20 - 3.16 mA':   '20',
                        '21 - 10 mA':     '21',
                        '22 - 31.6 mA':   '22',}
    
    ExcitRange_asList = list(ExcitRangeList)
    
    Tdelay = Float(0.01, label="Delay", desc="delay between scans [s]")
    Tmeas = Float(0, label="Delay", desc="delay between measurements [s]")
    Nscans = Int(1, label="fast Scans", desc="number of scans per point")
    Nscans_stable = Float(5, label="slow Scans", desc="number of scans per point during slow scanning time")
    stblz_time = Int(20, label="Fast scanning time", desc="If current control is activated: Time before and after current is applied\nTime duration where the number of scans is equal to fastScans [s]")
    stable_time = Int(10, label="Slow scanning time", desc="Time duration where the number of scans is equal to slowScans [s] \n (only takes effect if current control is off)")
    curr_scans = 1
    disable_switching = Bool(False, label="Only use slow Scans", desc="Disables switching between the number of scans and only uses the value defined in slow Scans")
    
    #+++++++++++ Channel 1 ++++++++++++
    
    Channel_1 = Bool(True, label="Channel #1", desc="channel #1 on/off")
    ResRange_1 = Trait('1 - 2 mOhm',ResRangeList, label="Resistance range", desc = "resistance range")
    ExcitRange_1 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range ", desc = "excitation range")
    ExcitMode_1 = Trait('Current excitation',{"Voltage excitation": '0', "Current excitation": '1',}, label = "Excitation mode", desc = "voltage/current excitation mode")
    Autorange_1 = Bool(False, label="Autorange", desc="autorange on/off")
    ### extra features ###
    Filter_1 = Bool(False, label= "Filter #1", desc="Filter for Channel #1 on/off")
    SetlTime_1 = Int(3, label="Settling Time (fast acquisition)", desc="Enter the settling time")
    SetlTime_1_slow = Int(30, label="Settling Time (slow acquisition)", desc="Enter the settling time")
    Window_1 = Int(10, label="Window (fast acquisition)", desc="Enter the filter window (in %)")
    Window_1_slow = Int(10, label="Window (slow acquisition)", desc="Enter the filter window (in %)")
    ### increment current
    Range_active_1 = Bool(False, label="Increment current")
    Inc_itr_1 = Int(10, label="# meas. per curr.", desc="Specifies repetition measurement for each interval")
    Start_erange_1 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range start", desc = "excitation range start")
    End_erange_1 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range end", desc = "excitation range end")
    
    #+++++++++++ Channel 2 ++++++++++++
    
    Channel_2 = Bool(False, label="Channel #2", desc="channel #2 on/off")
    ResRange_2 = Trait('1 - 2 mOhm',ResRangeList, label="Resistance range", desc = "resistance range")
    ExcitRange_2 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range ", desc = "excitation range")
    ExcitMode_2 = Trait('Current excitation',{"Voltage excitation": '0', "Current excitation": '1',}, label = "Excitation mode", desc = "voltage/current excitation mode")
    Autorange_2 = Bool(False, label="Autorange", desc="autorange on/off")
    ### extra features ###
    Filter_2 = Bool(False, label= "Filter #2", desc="Filter for Channel #2 on/off")
    SetlTime_2 = Int(30, label="Settling Time", desc="Enter the settling time")
    Window_2 = Int(10, label="Window", desc="Enter the filter window (in %)")
    ### increment current
    Range_active_2 = Bool(False, label="Increment current")
    Inc_itr_2 = Int(10, label="# meas. per curr.", desc="Specifies the time (in iterations) for each interval with the same current")
    Start_erange_2 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range start", desc = "excitation range start")
    End_erange_2 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range end", desc = "excitation range end")

    #+++++++++++ Channel 3 ++++++++++++
    
    Channel_3 = Bool(False, label="Channel #3", desc="channel #3 on/off")
    ResRange_3 = Trait('1 - 2 mOhm',ResRangeList, label="Resistance range", desc = "resistance range")
    ExcitRange_3 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range ", desc = "excitation range")
    ExcitMode_3 = Trait('Current excitation',{"Voltage excitation": '0', "Current excitation": '1',}, label = "Excitation mode", desc = "voltage/current excitation mode")
    Autorange_3 = Bool(False, label="Autorange", desc="autorange on/off")
    ### extra features ###
    Filter_3 = Bool(False, label= "Filter #3", desc="Filter for Channel #3 on/off")
    SetlTime_3 = Int(30, label="Settling Time", desc="Enter the settling time")
    Window_3 = Int(10, label="Window", desc="Enter the filter window (in %)")
    ### increment current
    Range_active_3 = Bool(False, label="Increment current")
    Inc_itr_3 = Int(10, label="# meas. per curr.", desc="Specifies the time (in iterations) for each interval with the same current")
    Start_erange_3 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range start", desc = "excitation range start")
    End_erange_3 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range end", desc = "excitation range end")

    #+++++++++++ Channel 4 ++++++++++++
    
    Channel_4 = Bool(False, label="Channel #4", desc="channel #4 on/off")
    ResRange_4 = Trait('1 - 2 mOhm',ResRangeList, label="Resistance range", desc = "resistance range")
    ExcitRange_4 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range ", desc = "excitation range")
    ExcitMode_4 = Trait('Current excitation',{"Voltage excitation": '0', "Current excitation": '1',}, label = "Excitation mode", desc = "voltage/current excitation mode")
    Autorange_4 = Bool(False, label="Autorange", desc="autorange on/off")
    ### extra features ###
    Filter_4 = Bool(False, label= "Filter #4", desc="Filter for Channel #4 on/off")
    SetlTime_4 = Int(30, label="Settling Time", desc="Enter the settling time")
    Window_4 = Int(10, label="Window", desc="Enter the filter window (in %)")
    ### increment current
    Range_active_4 = Bool(False, label="Increment current")
    Inc_itr_4 = Int(10, label="# meas. per curr.", desc="Specifies the time (in iterations) for each interval with the same current")
    Start_erange_4 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range start", desc = "excitation range start")
    End_erange_4 = Trait('1 - 1.00 pA', ExcitRangeList,label="Excitation range end", desc = "excitation range end")
    
    traits_view = View(Group(Include('chan1_group'),Include('chan2_group'),Include('chan3_group'),Include('chan4_group'),Include('common_group')),\
    style='custom',resizable=True, scrollable = True)

    width = 400
    chan1_group = Group('Channel_1',Group(Group(Item('ResRange_1', width = width),\
                Item('ExcitRange_1', style = "simple", width = width),Group('Autorange_1','ExcitMode_1',style="custom"), layout='split', style='simple', label = 'Ranges'),\
            Group(Item('Filter_1'), Group(Item('SetlTime_1'), Item('SetlTime_1_slow'), Item('Window_1'), Item('Window_1_slow'), enabled_when='Filter_1'),
                show_border = False, label = 'Filter'),\
            Group(Item('Range_active_1'), Group(Item('Start_erange_1'), Item('End_erange_1'), Item('Inc_itr_1'), enabled_when='Range_active_1'), 
                  show_border = False, label = 'Increment'),\
        layout = 'tabbed', orientation='horizontal', enabled_when='Channel_1'),
    style='simple',show_border=True)

    chan2_group = Group('Channel_2',Group(Group(Item('ResRange_2', width = width),\
                Item('ExcitRange_2', style = "simple", width = width),Group('Autorange_2','ExcitMode_2',style="custom"), layout='split', style='simple'),\
            Group(Item('Filter_2'), Group(Item('SetlTime_2'), Item('Window_2'), enabled_when='Filter_2'),
                show_border = False, label = 'Filter'),\
            Group(Item('Range_active_2'), Group(Item('Start_erange_2'), Item('End_erange_2'), Item('Inc_itr_2'), enabled_when='Range_active_2'), 
                  show_border = False, label = 'Increment'),\
        layout = 'tabbed', orientation='horizontal', enabled_when='Channel_2'),
    style='simple',show_border=True)

    chan3_group = Group('Channel_3',Group(Group(Item('ResRange_3', width = width),\
                Item('ExcitRange_3', style = "simple", width = width),Group('Autorange_3','ExcitMode_3',style="custom"), layout='split', style='simple', label = 'Ranges'),\
            Group(Item('Filter_3'), Group(Item('SetlTime_3'), Item('Window_3'), enabled_when='Filter_3'),
                show_border = False, label = 'Filter'),\
            Group(Item('Range_active_3'), Group(Item('Start_erange_3'), Item('End_erange_3'), Item('Inc_itr_3'), enabled_when='Range_active_3'), 
                  show_border = False, label = 'Increment'),\
        layout = 'tabbed', orientation='horizontal', enabled_when='Channel_3'),
    style='simple',show_border=True)

    chan4_group = Group('Channel_4',Group(Group(Item('ResRange_4', width = width),\
                Item('ExcitRange_4', style = "simple", width = width),Group('Autorange_4','ExcitMode_4',style="custom"), layout='split', style='simple', label = 'Ranges'),\
            Group(Item('Filter_4'), Group(Item('SetlTime_4'), Item('Window_4'), enabled_when='Filter_4'),
                show_border = False, label = 'Filter'),\
            Group(Item('Range_active_4'), Group(Item('Start_erange_4'), Item('End_erange_4'), Item('Inc_itr_4'), enabled_when='Range_active_4'), 
                  show_border = False, label = 'Increment'),\
        layout = 'tabbed', orientation='horizontal', enabled_when='Channel_4'),
    style='simple',show_border=True)
 
    common_group = Group(Item('Tdelay',  width=width), Item('Tmeas',  width=width), Item('Nscans_stable', width=width), Item('Nscans', width=width), 
                         Item('stblz_time', width=width) , Item('stable_time', width=width), Item('disable_switching'), show_border=False)

    def initialize(self):
        # self.ac=rm.open_resource('GPIB0::13::INSTR')
        # self.ac=rm.open_resource('GPIB1::1::INSTR')
        self.MS = ls370(address='13', gpib='GPIB0') #4 Underground
        # self.MS = ls370(address='1', gpib='GPIB1') #shielded room
        
        if self.Channel_1:
            self.MS.setResRange(channel='1',mode=self.ExcitMode_1_,excitRange=self.ExcitRange_1_,resRange=self.ResRange_1_, autorange='0', csOff='0')
            sleep(0.001)
            if(self.Filter_1):
                self.MS.setFilter(channel='1', on= 1, setlT=self.SetlTime_1, wind=self.Window_1)
            else:
                # print(self.SetlTime_1)
                self.MS.setFilter(channel='1', on= 0, setlT=self.SetlTime_1, wind=self.Window_1)

        if self.Channel_2:
            self.MS.setResRange(channel='2',mode=self.ExcitMode_2_,excitRange=self.ExcitRange_2_,resRange=self.ResRange_2_, autorange='0', csOff='0')
            sleep(0.001)
            if(self.Filter_2):
                self.MS.setFilter(channel='2', on= 1, setlT=self.SetlTime_2, wind=self.Window_2)
            else:
                self.MS.setFilter(channel='2', on= 0, setlT=self.SetlTime_2, wind=self.Window_2)

        if self.Channel_3:
            self.MS.setResRange(channel='3',mode=self.ExcitMode_3_,excitRange=self.ExcitRange_3_,resRange=self.ResRange_3_, autorange='0', csOff='0')
            sleep(0.001)
            if(self.Filter_3):
                self.MS.setFilter(channel='3', on= 1, setlT=self.SetlTime_3, wind=self.Window_3)
            else:
                self.MS.setFilter(channel='3', on= 0, setlT=self.SetlTime_3, wind=self.Window_3)

        if self.Channel_4:
            self.MS.setResRange(channel='4',mode=self.ExcitMode_4_,excitRange=self.ExcitRange_4_,resRange=self.ResRange_4_, autorange='0', csOff='0')
            sleep(0.001)
            if(self.Filter_4):
                self.MS.setFilter(channel='4', on= 1, setlT=self.SetlTime_4, wind=self.Window_4)
            else:
                self.MS.setFilter(channel='4', on= 0, setlT=self.SetlTime_4, wind=self.Window_4)
                
    def updateExcRang(self, itr):
        curr_time = ctime()
        if self.Range_active_1 and int(self.ExcitRange_1_) < int(self.End_erange_1_) and itr % self.Inc_itr_1 == 0:
            print(f"[{curr_time}] updating from {self.ExcitRange_asList[int(self.ExcitRange_1_)-1]} to {self.ExcitRange_asList[int(self.ExcitRange_1_)]}")
            # res_s = f"{curr_time}\t [updating from {self.ExcitRange_asList[int(self.ExcitRange_1_)-1]} to {self.ExcitRange_asList[int(self.ExcitRange_1_)]}]"
            self.ExcitRange_1 = self.ExcitRange_asList[int(self.ExcitRange_1_)] #update the ExciteRange Trait
            # return res_s
            
        if self.Range_active_2 and int(self.ExcitRange_2_) < int(self.End_erange_2_) and itr % self.Inc_itr_2 == 0:
            print(f"[{curr_time}] updating from {self.ExcitRange_asList[int(self.ExcitRange_2_)-1]} to {self.ExcitRange_asList[int(self.ExcitRange_2_)]}")
            self.ExcitRange_2 = self.ExcitRange_asList[int(self.ExcitRange_2_)] #update the ExciteRange Trait
            
        if self.Range_active_3 and int(self.ExcitRange_3_) < int(self.End_erange_3_) and itr % self.Inc_itr_3 == 0:
            print(f"[{curr_time}] updating from {self.ExcitRange_asList[int(self.ExcitRange_3_)-1]} to {self.ExcitRange_asList[int(self.ExcitRange_3_)]}")
            self.ExcitRange_3 = self.ExcitRange_asList[int(self.ExcitRange_3_)] #update the ExciteRange Trait
            
        if self.Range_active_4 and int(self.ExcitRange_4_) < int(self.End_erange_4_) and itr % self.Inc_itr_4 == 0:
            print(f"[{curr_time}] updating from {self.ExcitRange_asList[int(self.ExcitRange_4_)-1]} to {self.ExcitRange_asList[int(self.ExcitRange_4_)]}")
            self.ExcitRange_4 = self.ExcitRange_asList[int(self.ExcitRange_4_)] #update the ExciteRange Trait
              
        
    def getStableTime(self):
        return min(self.Inc_itr_1, self.Inc_itr_2, self.Inc_itr_3, self.Inc_itr_4)
    
    def getCurrent(self):
        # return self.ExcitRange_asList[int(self.ExcitRange_1_)-1].split(' - ')[1]
        return self.conv_to_pa(self.ExcitRange_asList[int(self.ExcitRange_1_)-1].split(' - ')[1])
    
    def conv_to_pa(self, amp):
        amps = amp.split()
        match amps[1]:
            case "pA":
                return float(amps[0])
            case "nA":
                return float(amps[0])*1000
            case "":
                return float(amps[0])*10e6
            case "mA":
                return float(amps[0])*10e9

###############################################################################################################################
    #Functions that get called if one of the fields in one of the Channels is updated (real time update of values)
    @observe('ExcitRange_1')
    def update_1_excr(self, event):
        # print(f"updating from {self.ExcitRangeList[event.old]} to {self.ExcitRangeList[event.new]}/{self.ExcitMode_1_}")        
        try:
            
            self.MS.setResRange(channel='1',mode=self.ExcitMode_1_,excitRange=self.ExcitRangeList[event.new],resRange=self.ResRange_1_, autorange='0', csOff='0')
            # scans_thread = WaitNsetThread(self)
            # scans_thread.start()
        except Exception as e:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass

    @observe('ResRange_1')
    def update_1_resr(self, event):
        # print(f"updating from {self.ResRangeList[event.old]} to {self.ResRangeList[event.new]}/{self.ExcitMode_1_}")
        try:
            self.MS.setResRange(channel='1',mode=self.ExcitMode_1_,excitRange=self.ExcitRange_1_,resRange=self.ResRangeList[event.new], autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
        
    exc_mode_dic = {"Voltage excitation": '0', "Current excitation": '1'}
    @observe('ExcitMode_1')
    def update_1_mode(self, event):
        # print(f"updating from {self.exc_mode_dic[event.old]} to {self.exc_mode_dic[event.new]}/{self.ExcitMode_1_}")
        try: 
            self.MS.setResRange(channel='1',mode=self.exc_mode_dic[event.new],excitRange=self.ExcitRange_1_,resRange=self.ResRange_1_, autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
        
    @observe('Filter_1')
    def toggleFilter1(self, event):
        try:
            self.MS.setFilter(channel='1', on=int(event.new), setlT=self.SetlTime_1, wind=self.Window_1_)
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
        
    @observe('Start_erange_1')
    def update_excr_1(self, event):
        self.ExcitRange_1 = self.ExcitRange_asList[int(self.Start_erange_1_) - 1]
        if int(self.End_erange_1_) < int(self.Start_erange_1_):
            self.End_erange_1 = self.ExcitRange_asList[int(self.Start_erange_1_) - 1]
        
    #Channel 2
    @observe('ExcitRange_2')
    def update_2_excr(self, event):
        # print(f"updating from {self.ExcitRangeList[event.old]} to {self.ExcitRangeList[event.new]}/{self.ExcitMode_2_}")
        try:
            self.MS.setResRange(channel='2',mode=self.ExcitMode_2_,excitRange=self.ExcitRangeList[event.new],resRange=self.ResRange_2_, autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
    
    @observe('ResRange_2')
    def update_2_resr(self, event):
        # print(f"updating from {self.ResRangeList[event.old]} to {self.ResRangeList[event.new]}/{self.ExcitMode_2_}")
        try:
            self.MS.setResRange(channel='2',mode=self.ExcitMode_2_,excitRange=self.ExcitRange_2_,resRange=self.ResRangeList[event.new], autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
        
    exc_mode_dic = {"Voltage excitation": '0', "Current excitation": '1'}
    @observe('ExcitMode_2')
    def update_2_mode(self, event):
        # print(f"updating from {self.exc_mode_dic[event.old]} to {self.exc_mode_dic[event.new]}/{self.ExcitMode_2_}")
        try:
            self.MS.setResRange(channel='2',mode=self.exc_mode_dic[event.new],excitRange=self.ExcitRange_2_,resRange=self.ResRange_2_, autorange='0', csOff='0')
        except: 
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
                    
    @observe('Filter_2')
    def toggleFilter2(self, event):
        try:
            self.MS.setFilter(channel='2', on=int(event.new), setlT=self.SetlTime_2_, wind=self.Window_2_)
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
            
    @observe('Start_erange_2')
    def update_excr_2(self, event):
        self.ExcitRange_2 = self.ExcitRange_asList[int(self.Start_erange_2_) - 1]
        if int(self.End_erange_2_) < int(self.Start_erange_2_):
            self.End_erange_2 = self.ExcitRange_asList[int(self.Start_erange_2_) - 1]
            
    #Channel 3
    @observe('ExcitRange_3')
    def update_3_excr(self, event):
        # print(f"updating from {self.ExcitRangeList[event.old]} to {self.ExcitRangeList[event.new]}/{self.ExcitMode_3_}")
        try:
            self.MS.setResRange(channel='3',mode=self.ExcitMode_3_,excitRange=self.ExcitRangeList[event.new],resRange=self.ResRange_3_, autorange='0', csOff='0')
        except: 
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
            
    @observe('ResRange_3')
    def update_3_resr(self, event):
        # print(f"updating from {self.ResRangeList[event.old]} to {self.ResRangeList[event.new]}/{self.ExcitMode_3_}")
        try:
            self.MS.setResRange(channel='3',mode=self.ExcitMode_3_,excitRange=self.ExcitRange_3_,resRange=self.ResRangeList[event.new], autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
        
    exc_mode_dic = {"Voltage excitation": '0', "Current excitation": '1'}
    @observe('ExcitMode_3')
    def update_3_mode(self, event):
        # print(f"updating from {self.exc_mode_dic[event.old]} to {self.exc_mode_dic[event.new]}/{self.ExcitMode_3_}")
        try:
            self.MS.setResRange(channel='3',mode=self.exc_mode_dic[event.new],excitRange=self.ExcitRange_3_,resRange=self.ResRange_3_, autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
        
    @observe('Filter_3')
    def toggleFilter3(self, event):
        try:
            self.MS.setFilter(channel='3', on=int(event.new), setlT=self.SetlTime_3_, wind=self.Window_3_)
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
            
    @observe('Start_erange_3')
    def update_excr_3(self, event):
        self.ExcitRange_3 = self.ExcitRange_asList[int(self.Start_erange_3_) - 1]
        if int(self.End_erange_3_) < int(self.Start_erange_3_):
            self.End_erange_3 = self.ExcitRange_asList[int(self.Start_erange_3_) - 1]
    
    #Channel 4
    @observe('ExcitRange_4')
    def update_4_excr(self, event):
        # print(f"updating from {self.ExcitRangeList[event.old]} to {self.ExcitRangeList[event.new]}/{self.ExcitMode_4_}")
        try:
            self.MS.setResRange(channel='4',mode=self.ExcitMode_4_,excitRange=self.ExcitRangeList[event.new],resRange=self.ResRange_4_, autorange='0', csOff='0')
        except: 
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
            
    @observe('ResRange_4')
    def update_4_resr(self, event):
        # print(f"updating from {self.ResRangeList[event.old]} to {self.ResRangeList[event.new]}/{self.ExcitMode_4_}")
        try:
            self.MS.setResRange(channel='4',mode=self.ExcitMode_4_,excitRange=self.ExcitRange_4_,resRange=self.ResRangeList[event.new], autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
        
    exc_mode_dic = {"Voltage excitation": '0', "Current excitation": '1'}
    @observe('ExcitMode_4')
    def update_4_mode(self, event):
        # print(f"updating from {self.exc_mode_dic[event.old]} to {self.exc_mode_dic[event.new]}/{self.ExcitMode_4_}")
        try:
            self.MS.setResRange(channel='4',mode=self.exc_mode_dic[event.new],excitRange=self.ExcitRange_4_,resRange=self.ResRange_4_, autorange='0', csOff='0')
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
            
    @observe('Filter_4')
    def toggleFilter4(self, event):
        try:
            # print(int(event.new))
            self.MS.setFilter(channel='4', on=int(event.new), setlT=self.SetlTime_4_, wind=self.Window_4_)
        except:
            # print("Update Error: Message could not be sent - either acquisition has not started or an error occured")
            pass
            
    @observe('Start_erange_4')
    def update_excr_4(self, event):
        self.ExcitRange_4 = self.ExcitRange_asList[int(self.Start_erange_4_) - 1]
        if int(self.End_erange_4_) < int(self.Start_erange_4_):
            self.End_erange_4 = self.ExcitRange_asList[int(self.Start_erange_4_) - 1]
################################################################################################################################

    def acquireALL(self, experiment,Frst):
        sleep(float(self.Tmeas))
        
        R1=0.0
        R2=0.0
        R3=0.0
        R4=0.0
        # print(self.MS.checkFilter('1'))
        if self.Channel_1:
            scan = False
            if (self.Channel_2 or self.Channel_3 or self.Channel_4) or Frst:
                scan = True
            R1 = self.MS.acquire(self.curr_scans, self.Tdelay, 1, scan)

        if self.Channel_2:
            scan = False
            if (self.Channel_2 or self.Channel_3 or self.Channel_4) or Frst:
                scan = True
            R2 = self.MS.acquire(self.curr_scans, self.Tdelay, 2, scan)

        if self.Channel_3:
            scan = False
            if (self.Channel_2 or self.Channel_3 or self.Channel_4) or Frst:
                scan = True
            R3 = self.MS.acquire(self.curr_scans, self.Tdelay, 3, scan)

        if self.Channel_4:
            scan = False
            if (self.Channel_2 or self.Channel_3 or self.Channel_4) or Frst:
                scan = True
            R4 = self.MS.acquire(self.curr_scans, self.Tdelay, 4, scan)

        return R1,R2,R3,R4

#! Threads and flow control

def process(image, results_obj):
    """ Function called to do the processing """
    X, Y = np.indices(image.shape) 
    x = sum(X*image)/sum(image)
    y = sum(Y*image)/sum(image)
    width = math.sqrt(abs(sum(((X-x)**2+(Y-y)**2)*image)/sum(image))) 
    results_obj.x = x
    results_obj.y = y
    results_obj.width = width
    
class CurrentSetThread(Thread):
    wants_abort = False
    
    def __init__(self, currentControl_inst, waitNsetThread_inst):
        super().__init__()
        self.daemon = True
        self.currentControl_inst = currentControl_inst
        self.waitNsetThread_inst = waitNsetThread_inst
    
    def run(self):
        #wait tBefore before setting the current
        # print(f"sleeping for {self.currentControl_inst.tBefore_s} seconds")
        self.active_sleep(self.currentControl_inst.tBefore_s)
        if self.wants_abort:
            return
        #begin the current setting loop
        for setcurrent in self.currentControl_inst.curr_list:
            self.currentControl_inst.CS.SetCurrent(setcurrent) 
            self.currentControl_inst.CS.ON()
            self.waitNsetThread_inst.current_on = True
            print(str(ctime())+' current on with I = '+str(setcurrent))
            #wait tOn with current on
            self.active_sleep(self.currentControl_inst.tOn_s)
            if self.wants_abort:
                return
            #switch current off
            self.currentControl_inst.CS.SetCurrent(0)
            self.currentControl_inst.CS.OFF()
            self.waitNsetThread_inst.current_on = False
            print(str(ctime())+' current off')
            #wait tOff with no current
            self.active_sleep(self.currentControl_inst.tOff_s)
        
        #switch current off at the end
        self.turnOff()
    
    def turnOff(self):
        setcurrent=0
        self.currentControl_inst.CS.SetCurrent(setcurrent)
        self.currentControl_inst.CS.OFF()
            
    def active_sleep(self, dur):
        curr_time = time()
        end_time = curr_time + dur
        while time() < end_time:
            if not self.wants_abort:
                sleep(0.01)
            else:
                return
        
#TODO implement logging to file of current from GS200 and voltage from Picoscope

class WaitNsetThread(Thread):
    """ This Thread waits for some custom time and then sets
        different number of scans, the filter and applies the current
    """
    wants_abort = False
    first = True
    current_on = False
    
    def __init__(self, ls370_inst, Nscans_fast, currentControl_inst):
        super().__init__()
        self.daemon = True
        self.ls370_inst = ls370_inst
        self.Nscans_fast = Nscans_fast
        self.paused = False
        self.currentControl_inst = currentControl_inst
        self.state = threading.Condition()
        if self.currentControl_inst.apply_curr:
            self.currSet = CurrentSetThread(self.currentControl_inst, self)
        
    
    def run(self):
        #start the current control thread
        if self.currentControl_inst.apply_curr:
            self.currSet.start()
            print("Started current control thread")
        #Start with fast scans before current is applied 
        if self.currentControl_inst.apply_curr:
            self.active_sleep(self.currentControl_inst.tBefore_s-self.ls370_inst.stblz_time-2)
        
        while not self.wants_abort:
            ##############pauses the thread if "Only use slow scans" is active##################
            with self.state:
                if self.paused:
                    self.state.wait()  # Block execution until notified.
            if self.wants_abort:
                if self.currentControl_inst.apply_curr:
                    self.currSet.wants_abort = True
                return
            ####################################################################################
            # print(f"switching to fast mode for {self.ls370_inst.stblz_time*2} seconds")
            #first apply the filter
            if self.ls370_inst.Filter_1:
                #sets the filter to fast mode
                self.ls370_inst.MS.setFilter(on=1,channel='1',setlT=self.ls370_inst.SetlTime_1, wind=self.ls370_inst.Window_1)
            self.active_sleep(2) #wait for filter
            self.ls370_inst.curr_scans = self.Nscans_fast #sets the scans to fast mode
                
            #check if it was not aborted before sleeping
            if not self.wants_abort:
                #sleep for user defined time stblz_time before and after the current change (fast mode)
                if self.currentControl_inst.apply_curr:
                    self.active_sleep(self.ls370_inst.stblz_time*2-2)
                else:
                    #if current control is not active, just wait for the given time
                    self.active_sleep(self.ls370_inst.stblz_time-2)
                ######################check if functionality aborted#####################
                with self.state:
                    if self.paused:
                        self.state.wait()  # Block execution until notified.
                        break
                if self.wants_abort:
                    return
                #########################################################################
                #update to slow mode
                #first set filter to slow mode
                
                if self.ls370_inst.Filter_1:
                    #set the filter to slow mode
                    self.ls370_inst.MS.setFilter(on=1,channel='1',setlT=self.ls370_inst.SetlTime_1_slow, wind=self.ls370_inst.Window_1_slow)
                self.active_sleep(2) #wait for filter
                self.ls370_inst.curr_scans = int(self.ls370_inst.Nscans_stable)
                
            else:
                if self.currentControl_inst.apply_curr:
                    self.currSet.wants_abort = True
                return        
            # self.active_sleep(self.ls370_inst.stable_time) #old implementation
            #sleep with slow mode on between the current changes
            if self.currentControl_inst.apply_curr and self.current_on:
                # print(f"Switching to slow mode for {self.currentControl_inst.tOn_s - 2*self.ls370_inst.stblz_time} seconds")
                self.active_sleep(self.currentControl_inst.tOn_s - 2*self.ls370_inst.stblz_time-2)
            elif self.currentControl_inst.apply_curr and not self.current_on:
                # print(f"Switching to slow mode for {self.currentControl_inst.tOff_s - 2*self.ls370_inst.stblz_time} seconds")
                self.active_sleep(self.currentControl_inst.tOff_s - 2*self.ls370_inst.stblz_time-2)
            else:
                self.active_sleep(self.ls370_inst.stable_time-2)
            
        #restart the function after breaking
        if not self.wants_abort:
            self.run()
    
    def pause(self):
        with self.state:
            self.paused = True  # Block self.

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()  # Unblock self if waiting.
    
    def active_sleep(self, dur):
        curr_time = time()
        end_time = curr_time + dur
        while time() < end_time:
            if not self.wants_abort:
                sleep(0.01)
            else:
                if self.currentControl_inst.apply_curr:
                    self.currSet.wants_abort = True
                return

class AcquisitionThread(Thread):
    """ Acquisition loop. This is the worker thread that retrieves data 
        from the ls370 bridge, displays them, and spawns the processing job.
    """
    wants_abort = False

    def process(self, image):
        """ Spawns the processing job.
        """
        try:
            if self.processing_job.is_alive():
                self.display("Processing to slow")
                return
        except AttributeError:
            pass
        self.processing_job = Thread(target=process, args=(image,
                                                            self.results))
        self.processing_job.start()

    def run(self):
        
        
        """ Runs the acquisition loop.
        """

        res1 = []
        res2 = []
        res3 = []
        res4 = []
        
        tm = []

        First = True

        try:
            self.display('Checking connection to 370 AC Resistance Bridge ...')
            self.initialize_ac()
        except pyvisa.VisaIOError as e:
            self.display('Problem while connecting to AC bridge LS370!')
            self.wants_abort = True
            
        else:
            self.display('AC bridge connected.')
            self.display('Data acquisition started')
        
        # if self.currentControl_inst.apply_curr:
        try: 
            self.initialize_current()
        except:
            self.display('Problem while connecting to Picoscope or Current source')

        dir_test = 'K:\\Data ac370\\'
        dir = datetime.datetime.now().date().__str__() 

        # datafile = dir_test + dir+'_Cp_'+'RuO2_holder_heater_cal_heating_test'+'.dat'
        datafile = self.f_name
        fileMode = 'a'

        try:
            fout = open(datafile, fileMode)
            head = "#Time\tR1\tR2\tR3\tR4"
            fout.write("#"+dir+"\n")
            fout.write(head+"\n")
            fout.write("Res,I Ch1: %s\t%s\t Ch2: %s\t%s\t Ch3: %s\t%s\t Ch4: %s\t%s\t\n" % (self.param[4],self.param[0],self.param[5],self.param[1],self.param[6],self.param[2],self.param[7],self.param[3]))
        except Exception as e:
            self.display('Output file open error: %s' % str(e))
            self.wants_abort = True

        itr = 0
        amp = int(self.getCurrent())
        self.ac_bridge.curr_scans = self.ac_bridge.Nscans #initialize the variable that tracks the current Nscans
        self.waitNsetThread = WaitNsetThread(self.ac_bridge, self.ac_bridge.Nscans, self.current_control)
        if not self.wants_abort and not self.ac_bridge.disable_switching:
            self.waitNsetThread.start()
            self.waitNsetThread.wants_abort = False
        #accumulation array
        acc_arr = []
        
        while not self.wants_abort:
            res =self.acquireALL(self.experiment, First)
            curr_time = time()
            
            #TODO Write output from GS200 and Picoscope to file
            if self.current_control.apply_curr:
                gs200_inst = self.current_control.CS
                picoscope_inst = self.current_control.VS
                gs200_I_meas = gs200_inst.GetCurrent()
                picoscope_v_meas = np.average(picoscope_inst.getData('A',5E5,int(1e5),resolution='16'))
            else:
                gs200_I_meas = 0.0
                picoscope_v_meas = 0.0

            #accumulate the values in arrays and only put them to the file every x iterations
            res_s = '%s\t%f\t%s \t%s\t%s\t%f\t%f\t%f\n' % (curr_time,res[0],amp,gs200_I_meas,picoscope_v_meas,res[1],res[2],res[3])
            acc_arr.append(res_s)
            x = 20
            if itr % x == 0 and itr != 0:
                with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        fout = open(datafile,"a")
                        for res_curr in acc_arr:
                                #Write to file, following colums: Time | AC370 Ch1 | I from AC370 | I from GS200 | V from Picoscope | AC370 Ch2 | AC370 Ch3 | AC370 Ch4
                                fout.write(res_curr)
                        fout.close()
                acc_arr = []
            
            #increment the current (if applicable)
            if itr % self.getStableTime() == 0 and itr != 0:
                # print(itr)
                self.updateExcRang(itr)
                amp = int(self.getCurrent())
                # self.display(res_s)
            
            #self.display('%s\t%f\t%s\t%s\t%s\t%f\t%f\t%f' % (ctime(curr_time),res[0],amp,gs200_I_meas,picoscope_v_meas,res[1],res[2],res[3]))
            res_s2 = '%s\t%f\t%s \t%s\t%s\t %f\t%f\t%f\n' % (ctime(curr_time),res[0],amp,gs200_I_meas,picoscope_v_meas,res[1],res[2],res[3])
            self.display(res_s2)
            
            tm.append(curr_time)
            res1.append(res[0])
            res2.append(res[1])
            res3.append(res[2])
            res4.append(res[3])            
            self.image1_show(tm,res1)
            self.image2_show(tm,res2)
            self.image3_show(tm,res3)
            self.image4_show(tm,res4)            

            First = False
            
            #if the switching is deactived in runtime
            if self.ac_bridge.disable_switching:
                self.waitNsetThread.pause()
                self.ac_bridge.curr_scans = self.ac_bridge.Nscans_stable
            
            #if the switching is reactivated the thread starts again
            if not self.ac_bridge.disable_switching:
                # print("resuming")
                self.waitNsetThread.resume()
            
            itr += 1

        # self.waitNsetThread.join()
        self.display('Data acquisition stopped')

#! The GUI elements

class ControlPanel(HasTraits):
    """ This object is the core of the traitsUI interface. Its view is
        the right panel of the application, and it hosts the method for
        interaction between the objects and the GUI.
    """
    dir = 'K:\\Data ac370\\'
    norm_file_name = datetime.datetime.now().date().__str__()+'_Cal_'+'Cp_227_New_60mK'+'.dat' 
    
    f_name = File(dir+norm_file_name)
    experiment = Instance(Experiment, ())
    ac_bridge = Instance(Bridge, ())
    figure1 = Figure()
    figure2 = Instance(Figure)
    figure3 = Instance(Figure)
    figure4 = Instance(Figure)
    results = Instance(Results, ())
    start_stop_acquisition = Button("Start/Stop acquisition")
    results_string =  String()
    acquisition_thread = Instance(AcquisitionThread)
    current_control = Instance(CurrentControl, ())
    
    
    view = View(Group(
                Group(
                    Group(
                        Item('start_stop_acquisition', show_label=False ),
                        Item('results_string',show_label=False, springy=True, style='custom')),
                  Item('f_name', label = "Save Location"),
                  label="Control", dock='tab',),
                Group(
                  Group(
                    Item('experiment', style='custom', show_label=False),
                    label="Input",),
                  Group(
                    Item('results', style='custom', show_label=False),
                    label="Results",),
                label='Experiment', dock="tab"),
                Item('ac_bridge', style='custom', show_label=False,
                                    dock="tab"),
                Item('current_control', style='custom', show_label=False),
               layout='tabbed'),
               )

    def _start_stop_acquisition_fired(self):
        """ Callback of the "start stop acquisition" button. This starts
            the acquisition thread, or kills it/
        """
        if self.acquisition_thread and self.acquisition_thread.is_alive():
            self.acquisition_thread.wants_abort = True
            self.acquisition_thread.waitNsetThread.wants_abort = True
            self.acquisition_thread.waitNsetThread.paused = False
            self.acquisition_thread.waitNsetThread.resume()
            if self.acquisition_thread.current_control.apply_curr:
                self.acquisition_thread.waitNsetThread.currSet.turnOff()
            self.acquisition_thread.waitNsetThread.join()
            self.ac_bridge.disable_switching = False
            # self.acquisition_thread.waitNsetThread.state.notify()
        else:
            self.acquisition_thread = AcquisitionThread()
            self.acquisition_thread.display = self.add_line
            self.acquisition_thread.initialize_ac = self.ac_bridge.initialize
            self.acquisition_thread.acquireALL = self.ac_bridge.acquireALL
            self.acquisition_thread.param = [self.ac_bridge.ExcitRange_1_,self.ac_bridge.ExcitRange_2_,self.ac_bridge.ExcitRange_3_,self.ac_bridge.ExcitRange_4_,
                                             self.ac_bridge.ResRange_1_,self.ac_bridge.ResRange_2_,self.ac_bridge.ResRange_3_,self.ac_bridge.ResRange_4_]
                                             #self.ac_bridge.SetlTime_1, self.ac_bridge.SetlTime_2_, self.ac_bridge.SetlTime_3_, self.ac_bridge.SetlTime_4_]
            self.acquisition_thread.experiment = self.experiment
            self.acquisition_thread.image1_show = self.image1_show
            self.acquisition_thread.image2_show = self.image2_show
            self.acquisition_thread.image3_show = self.image3_show
            self.acquisition_thread.image4_show = self.image4_show                        
            self.acquisition_thread.results = self.results
            self.acquisition_thread.getStableTime = self.ac_bridge.getStableTime
            self.acquisition_thread.updateExcRang = self.ac_bridge.updateExcRang
            self.acquisition_thread.getCurrent = self.ac_bridge.getCurrent
            self.acquisition_thread.f_name = self.f_name
            self.acquisition_thread.ac_bridge = self.ac_bridge
            self.acquisition_thread.current_control = self.current_control
            self.acquisition_thread.initialize_current = self.current_control.initialize
            self.acquisition_thread.start()
    
    def add_line(self, string):
        """ Adds a line to the textbox display.
        """
        self.results_string = (string + "\n" + self.results_string)[0:1000]


    def image1_show(self, tm, r1):
        # axes = self.figure1.axes[0]
        # axes.clear()
        # axes.plot(tm,r1,'r-o')
        # wx.CallAfter(self.figure1.canvas.draw)
        axes = self.figure1.axes[0]
        if axes.lines:
            line = axes.lines[0]
            line.set_xdata(tm)
            line.set_ydata(r1)
        else:
            axes.plot(tm, r1, 'r-o')
        axes.relim()
        axes.autoscale_view()
        # self.figure1.subplots_adjust(wspace = 0.2)#(left=0.5, right=0.6, top=0.95, bottom=0.15)
        # self.figure1.tight_layout()
        wx.CallAfter(self.figure1.canvas.draw)        

    def image2_show(self, tm, r2):
        # axes = self.figure2.axes[0]
        # axes.clear()
        # axes.plot(tm,r2,'b-o')
        # wx.CallAfter(self.figure2.canvas.draw)
        axes = self.figure2.axes[0]
        if axes.lines:
            line = axes.lines[0]
            line.set_xdata(tm)
            line.set_ydata(r2)
        else:
            axes.plot(tm, r2, 'b-o')
        axes.relim()
        axes.autoscale_view()
        wx.CallAfter(self.figure2.canvas.draw)

    def image3_show(self, tm, r3):
        # axes = self.figure3.axes[0]
        # axes.clear()
        # axes.plot(tm,r3,'g-o')
        # wx.CallAfter(self.figure3.canvas.draw)
        axes = self.figure3.axes[0]
        if axes.lines:
            line = axes.lines[0]
            line.set_xdata(tm)
            line.set_ydata(r3)
        else:
            axes.plot(tm, r3, 'g-o')
        axes.relim()
        axes.autoscale_view()
        wx.CallAfter(self.figure1.canvas.draw)

    def image4_show(self, tm, r4):
        # axes = self.figure4.axes[0]
        # axes.clear()
        # axes.plot(tm,r4,'-o')
        # wx.CallAfter(self.figure4.canvas.draw)
        axes = self.figure4.axes[0]
        if axes.lines:
            line = axes.lines[0]
            line.set_xdata(tm)
            line.set_ydata(r4)
        else:
            axes.plot(tm, r4, '-o')
        axes.relim()
        axes.autoscale_view()
        wx.CallAfter(self.figure4.canvas.draw)

class MainWindowHandler(Handler):
    def close(self, info, is_OK):
        if ( info.object.panel.acquisition_thread 
                        and info.object.panel.acquisition_thread.is_alive() ):
            info.object.panel.acquisition_thread.wants_abort = True
            while info.object.panel.acquisition_thread.is_alive():
                sleep(0.005)
            wx.Yield()
        return True


class MainWindow(HasTraits):
    """ The main window, here go the instructions to create and destroy
        the application.
    """
    figure1 = Instance(Figure)
    figure2 = Instance(Figure)
    figure3 = Instance(Figure)
    figure4 = Instance(Figure)    

    panel = Instance(ControlPanel)
    
    def adjust_subplots(self, figure):
        figure.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)

    def _figure1_default(self):
        figure1 = Figure()
        figure1.add_axes([0.1, 0.04, 0.9, 0.92])
        
        return figure1

    def _figure2_default(self):
        figure2 = Figure()
        figure2.add_axes([0.1, 0.04, 0.9, 0.92])
        return figure2

    def _figure3_default(self):
        figure3 = Figure()
        figure3.add_axes([0.1, 0.04, 0.9, 0.92])
        return figure3

    def _figure4_default(self):
        figure4 = Figure()
        figure4.add_axes([0.1, 0.04, 0.9, 0.92])
        return figure4


    def _panel_default(self):
        return ControlPanel(figure1=self.figure1,figure2=self.figure2,figure3=self.figure3,figure4=self.figure4)

    view = View(HSplit(  Group(Item('figure1',  editor=MPLFigureEditor(),
                                                        dock='tab',style='custom',show_label=False,),
                         Item('figure2',  editor=MPLFigureEditor(),
                                                        dock='tab',style='custom',show_label=False,),
                        Item('figure3',  editor=MPLFigureEditor(),
                                                        dock='tab',style='custom',show_label=False,),
                        Item('figure4',  editor=MPLFigureEditor(),
                                                        dock='tab',style='custom',show_label=False,),
                               layout='tabbed',dock='vertical'),
                        Item('panel', style="custom"),
                    show_labels=False, 
                    ),
                resizable=True, 
                height=0.77, width=0.75,
                handler=MainWindowHandler(),
                
                buttons=NoButtons)

if __name__ == '__main__':
    MainWindow().configure_traits()