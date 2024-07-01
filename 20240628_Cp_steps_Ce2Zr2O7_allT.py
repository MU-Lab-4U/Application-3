# -*- coding: utf-8 -*-
import os, sys, signal
import string
import pyreadline3 as readline
import traceback
import os.path as posixpath
import timeit, time
from datetime import datetime
import numpy.matlib as mat
import numpy as np
import scipy.optimize as scimin
from scipy import interpolate
import math
import fileinput
from msvcrt import getch

#from InstrumentsDryDilu import keithley6221, ls370, GS200, Picoscope
from instruments2 import keithley6221, ls370, GS200, Picoscope

    
def resistanceTempConversion(resistance):
    """
    conversion between a resistance into a temperature value according to this formula
     """
     
    ### new thermometer - T < 50mK 
    coef=[45649501181.2393,-57403689469.4274,28729283814.6464,-7115614068.2735,857772845.69161,-36600744.916129,-589518.974103669,0,0,0]
    ### new thermometer - T > 50mK
    #coef=[-4356963308.17082,7754260548.99398,-5404714604.46089,1589776465.43316,69013731.6432161,-205183999.460342,69461873.3528956,-11682127.4041518,1026592.12842404,-37704.6144473225]
        
    S=0
    lnR=math.log10(resistance-145)
    for i in range(10):
         S=S+coef[i]*lnR**i
        
    t=math.pow(10,S)/1000            

    return t#tempConversion
        

if __name__=='__main__':
    #Initialize instruments
    CS=GS200()
    MS=ls370()    ##T reading with LS 370 measure
    MS.ScanChannel('1','0')
    VS=Picoscope()
    VS.MeasParam('A')
    VS.MeasParam('B',en=False)
    VS.MeasParam('C',en=False)
    VS.MeasParam('D',en=False)
    print('Picoscope ok')
    
    
    base_path  = r'C:/Users/dnguyen/Documents/PythonProgram' 
        #Where to store data (should exist)
    tempRespPath  = r'/measurements'
    
    #arguments from the commandline
    # prefix = sys.argv[1]
    prefix = 'New CP'
    
    prefixFolderPath = base_path+tempRespPath+'/'+prefix

    if not posixpath.exists(prefixFolderPath):
        print( 'create folder: \''+prefixFolderPath+'\'')
        os.makedirs(prefixFolderPath)
    else:
        print( 'Folder \''+prefixFolderPath+'\' already exists')
    
    response_path = tempRespPath+'/'+prefix
    
     #########################
    #######MEASUREMENT#######
    #########################
    #~~-_-~~Important variables~~-_-~~#
    min_ini = 1    #minutes to measure before current
    min_Ion = 5  #minutes to measure with current on
    min_Ioff = 2*min_Ion    #minutes to measure after current off
    #setcurrentlist = [1e-6]
    current1 = 0.3e-6
    current2 = 0.5e-6
    current3 = 0.7e-6
    #variables for filter
    setl = [3,30,3] #first value corresponds to first settling time of filter and so on
    wind = [10,10,10] #the same with filter window size

    
    #T_start     = 0.1        #start temp [K] of the series of measurements (should be greater than 0 for logscale)
    #T_stop      = 0.2          #end temp [K] of the series of measurements
    #amountMeasPts = 2            #number of measuring points (incl. T_start and T_stop)
    #linearSweep = True 
    T_list = [0.016,0.04,0.05,0.075,0.1]
    #-----------------------------------#
    
    #determine the points at which temperature the measurements should be performed
    #if linearSweep == True:
    #    measTempPoints = np.linspace(T_start, T_stop, amountMeasPts, True)
    #else:
    #    measTempPoints = np.logspace(np.log10(T_start), np.log10(T_stop), num=amountMeasPts, base=10.0)
    #print( "Temperature from {}K to {}K -> {} steps".format(T_start, T_stop, amountMeasPts))
    
    #iMeas = 0
    #for iMeas < amountMeasPts:
    for iMeas in T_list:
        #iMeas=iMeas+1
        T0 = iMeas
    
        print( "Set Temperature to {}K".format(T0))
        PID_list = "0.0\t15000.0\t0.0\t"+str(T0*1000)+"\n"    
        with open('PID_curr_list_Cp_meas.txt', 'w', encoding='utf-8') as file:
            file.writelines(PID_list)
  
        #if iMeas != 0.02:
        print( "wait 1 min")
        time.sleep(60) # in seconds
        #else:
        #    time.sleep(60)
    
    
        datafile=base_path+response_path+'/TemperatureResponse_long_'+"{:.3f}".format(T0)+'.dat'
        data=open(datafile,"a+")
        data.write("t \t # \t R_Cp \t I \t U \n"+\
                       "unix_s \t - \t Ohm \t I \t V"+\
                       "\n")
        
        setcurrent=0
        
        for i in range(2):
            #measure before I is applied
            print(str(datetime.now())+' Start measuring pre I')
            t_end = time.time() + 60*min_ini
            #################set the filter###################
            MS.setFilter(on=1, channel = '1', setlT=setl[0], wind=wind[0])
            ###################################################
            while time.time() < t_end:
                ts1="%.2f" % time.time()
                mv='\t'+str(i)
                getR = float(MS.acquire(1,0.1,1))#Resistance of the thermometer  ##ToCheck
                mv+='\t'+str(getR)
                #calcTemp = float(resistanceTempConversion(getR))#convert the resistance into a temperature value
                #mv+='\t'+str(calcTemp)
                mv+='\t'+str(setcurrent)
                U=np.average(VS.getData('A',5E5,int(1e5)))
                mv+='\t'+str(U)
                
                fline=ts1.ljust(15)+mv+'\n'
                data.write(fline)
                data.flush()
                
                #time.sleep(0.5)
        
            #set I and measure
            if T0 <= 0.035:
                setcurrent=current1
            elif T0 <= 0.05: 
                setcurrent=current2
            else: 
                setcurrent=current3
            CS.SetCurrent(setcurrent)
            CS.ON()
            print(str(datetime.now())+' current on with I = '+str(setcurrent))
            t_end = time.time() + 60*min_Ion
            #################set the filter###################
            MS.setFilter(on=1, channel = '1', setlT=setl[0], wind=wind[1])
            ###################################################
            while time.time() < t_end:
                ts1="%.2f" % time.time()
                mv='\t'+str(i)
                getR = float(MS.acquire(1,0.01,1))#Resistance of the thermometer  ##ToCheck
                mv+='\t'+str(getR)
                #calcTemp = float(resistanceTempConversion(getR))#convert the resistance into a temperature value
                #mv+='\t'+str(calcTemp)
                mv+='\t'+str(setcurrent)
                U=np.average(VS.getData('A',5E5,int(1e5)))
                mv+='\t'+str(U)
                
                fline=ts1.ljust(15)+mv+'\n'
                data.write(fline)
                data.flush()
            
            setcurrent=0
            CS.SetCurrent(setcurrent)
            CS.OFF()
            print(str(datetime.now())+' current off')
            t_end = time.time() + 60*min_Ioff
            #################set the filter###################
            MS.setFilter(on=1, channel = '1', setlT=setl[1], wind=wind[2])
            ###################################################
            while time.time() < t_end:
                ts1="%.2f" % time.time()
                mv='\t'+str(i)
                getR = float(MS.acquire(30,0.01,1))#Resistance of the thermometer  ##ToCheck
                mv+='\t'+str(getR)
                #calcTemp = float(resistanceTempConversion(getR))#convert the resistance into a temperature value
                #mv+='\t'+str(calcTemp)
                mv+='\t'+str(setcurrent)
                U=np.average(VS.getData('A',5E5,int(1e5)))
                mv+='\t'+str(U)
                
                fline=ts1.ljust(15)+mv+'\n'
                data.write(fline)
                data.flush()
    
    T_finish = 16  #T setpoint [mK] after measurement finished
    PID_list = "0.0\t15000.0\t0.0\t"+str(T_finish)+"\n"
    with open('PID_curr_list_Cp_meas.txt', 'w', encoding='utf-8') as file:
        file.writelines(PID_list)
    
    print('Measurement finished at '+str(datetime.now()))
            
 