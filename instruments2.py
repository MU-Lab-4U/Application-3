# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 08:17:18 2017
Updated on Mon Jun 3 16:44:30 2024 

@author: andrey
"""
import serial
import time
import serial
from tqdm import tqdm
import numpy as npy
import sys
import pyvisa
# rm = pyvisa.ResourceManager(r"C:\WINDOWS\system32\agvisa32.dll")
rm = pyvisa.ResourceManager()
lib = rm.visalib


# Special characters: command end or command separators
SPECIAL_CHARACTERS = {
    'CR':  "\x0D",  # Carriage Return
    'LF':  "\x0A",  # Line Feed
    'HT': "\x09",  # Command Separator
    'SPACE': "\x20",  # Empty Character Place
}

LINE_TERMINATION = SPECIAL_CHARACTERS['LF']

SYMBOL_ON_OFF = {
    'ON': "1",
    'OFF': "0",
    'on': "1",
    'off': "0",
    '1': "1",
    '0': "0",
}


class TripleCS(object):
    def __init__(self, serialPort, baud=9600, debug=False):
        self.debug = debug
        try:
            self.connection = serial.Serial(
                port=serialPort, baudrate=baud, bytesize=8, parity='N', stopbits=1, timeout=1)
        except serial.serialutil.SerialException as se:
            print('connection did not work')
            raise se
            exit()
    #    try:
    #        self.connection.open()
    #    except Exception, e:
    #        print "error open serial port: " + str(e)
    #        exit()

        if self.connection.isOpen():
            try:
                self.connection.flushInput()  # flush input buffer, discarding all its contents
                self.connection.flushOutput()  # flush output buffer, aborting current output

                encoded = bytes("ID?"+LINE_TERMINATION, 'utf-8')
                self.connection.write(encoded)
                tmp = self.connection.readline()
                ID_str = tmp.split(bytes(SPECIAL_CHARACTERS['HT'], 'utf-8'))[1]
                print(("Triple CS connected: ID - %s") % str(ID_str))
                time.sleep(0.5)

            except Exception as e:
                print("error communicating...: " + str(e))

        self.logfilename = ''

    def setSorb(self, current):
        """
        set Sorb current in uA
        """
        encoded = bytes("SETDAC 1 0 " + str(current)+LINE_TERMINATION, 'utf-8')
        self.connection.write(encoded)
        status = self.connection.readline()

    def setStill(self, current):
        """
        set Still current in uA
        """
        not_encoded = "SETDAC 2 0 " + str(current)+LINE_TERMINATION
        encoded = bytes("SETDAC 2 0 " + str(current)+LINE_TERMINATION, 'utf-8')
        self.connection.write(encoded)
        status = self.connection.readline()

    def setMixingChamber(self, current):
        """
        set Mixing Chamber current in uA
        """
        # encoded = ("SETDAC 3 0 " + str(current)+ LINE_TERMINATION).write(serial.cmd.encode())
        not_encoded = "SETDAC 3 0" + str(current) + LINE_TERMINATION
        encoded = bytes("SETDAC 3 0 " + str(current)+ "\x0A", 'utf-8')
        self.connection.write(encoded)
        status = self.connection.readline()
        # print(encoded)

    def toggle(self, sorb, still, mc):
        """
        """
        sorb_str = SYMBOL_ON_OFF[str(sorb)]
        still_str = SYMBOL_ON_OFF[str(still)]
        mc_str = SYMBOL_ON_OFF[str(mc)]

        encoded = bytes('SETUP 0,0,'+sorb_str+',0,0,0,' +
                              still_str+',0,0,0,'+mc_str+',0'+LINE_TERMINATION, 'utf-8')
        self.connection.write(encoded)
        status = self.connection.readline()
        self.check_status()

    def sorb(self, sorb='OFF'):
        sorb_str = SYMBOL_ON_OFF[str(sorb)]
        sorb_status = self.check_status()[0]
        if sorb_status != sorb_str:
            encoded = bytes('SETUP 0,0,1,0,0,0,0,0,0,0,0,0' + LINE_TERMINATION, 'utf-8')
            self.connection.write(encoded)
            status = self.connection.readline()

    def still(self, still='OFF'):
        still_str = SYMBOL_ON_OFF[str(still)]
        still_status = self.check_status()[1]
        if still_status != still_str:
            encoded = bytes('SETUP 0,0,0,0,0,0,1,0,0,0,0,0' + LINE_TERMINATION, 'utf-8')
            self.connection.write(encoded)
            status = self.connection.readline()

    def mixingchamber(self, mc='OFF'):
        mc_str = SYMBOL_ON_OFF[str(mc)]
        mc_status = self.check_status()[2]
        if mc_status != mc_str:
            encoded = bytes('SETUP 0,0,0,0,0,0,0,0,0,0,1,0' + LINE_TERMINATION, 'utf-8')
            # print(encoded)
            self.connection.write(encoded)
            status = self.connection.readline()
            

    def check_status(self):
        encoded = bytes('STATUS?' + LINE_TERMINATION, 'utf-8')
        self.connection.write(encoded)
        tmp = self.connection.readline()
        # print(tmp)
        status_all = tmp.split(bytes(SPECIAL_CHARACTERS['HT'], 'utf-8'))[1]
        status = status_all.split(bytes(',', 'utf-8'))
        cs_status = status[0]
        sorb_status = status[3]
        still_status = status[7]
        mc_status = status[11]
        return sorb_status, still_status, mc_status

    def close(self):
        self.connection.close()

    def __del__(self):
        self.close()


class SX199(object):
    '''
'''

    def __init__(self, address='5', **kwargs):
        try:
            print("Checking connection to SX199 ...")
            # self.sx=instrument('GPIB1::'+address+'::INSTR',**kwargs)
            self.sx = rm.open_resource('GPIB1::'+address+'::INSTR', **kwargs)
        except pyvisa.VisaIOError as e:
            print("Problem while connecting to SX199: %s" % e)
        else:
            print("SX199 is connected. Continue ...")

    def link_to_port(self, port='1'):
        self.sx.write('LINK ' + str(port))
        self.sx.write(LINE_TERMINATION)

    def unlink(self):
        self.sx.write('!a')

    def clean_error(self):
        self.sx.write('*ESR?')
        self.sx.write(LINE_TERMINATION)

    def error(self):
        self.sx.write('LCME?')
        self.sx.write(LINE_TERMINATION)

    def CS580_set_gain(self, gain='0'):
        self.sx.write('GAIN '+str(gain))
        self.sx.write(LINE_TERMINATION)

    def CS580_input(self, inpt='OFF'):
        self.sx.write('INPT '+inpt)
        self.sx.write(LINE_TERMINATION)

    def CS580_output(self, sout='OFF'):
        self.sx.write('SOUT '+sout)
        self.sx.write(LINE_TERMINATION)

    def CS580_get_gain(self):
        self.sx.write('GAIN?')
        # self.sx.write(LINE_TERMINATION)
        g = self.sx.read()

        return g

    def send_cmd(self, cmd):
        self.sx.write(cmd)
        self.sx.write(LINE_TERMINATION)

    def read(self):
        self.sx.read()

class WF1974(object):
    '''
'''
    def __init__(self,gpib_address='15', **kwargs):
        try:
            print("Checking connection to WF1974 ...")
            self.nf=rm.open_resource('GPIB1::'+gpib_address+'::INSTR',**kwargs)
        except pyvisa.VisaIOError as e:
            print("Problem while connecting to WF1974: %s" %e)
        else:
            print("WF1974 is connected. Continue ...")
#            self.nf.write('*RST; *WAI')
            self.nf.write('SOUR:VOLT:AMPL:UNIT VRMS')
            self.nf.write('SOUR:VOLT:OFFS 0')
            self.nf.write('SOUR:FREQ:UNIT HZ')
            self.nf.write('SOUR:FREQ:MODE CW')
            self.nf.write('SOUR:PHAS 0')

    def outputOn(self):
        self.nf.write('OUTP ON')

    def outputOFF(self):
        self.nf.write('OUTP OFF')

    def setFreq(self, freq):
        self.nf.write('SOUR:FREQ '+freq)

    def setAmpl(self, ampl):
        self.nf.write('SOUR:VOLT '+ampl)


class SR7124(object):
    '''
'''

    def __init__(self, ip_address='10.0.0.8', **kwargs):
        try:
            print("Checking connection to 7124 ...")
            # self.la=instrument('TCPIP0::'+ip_address+'::50000::SOCKET',term_chars='\x00',send_end=True,timeout=20,**kwargs)
            self.la = rm.open_resource(
                'TCPIP0::'+ip_address+'::50000::SOCKET', **kwargs)
            self.la.timeout = 20000  # ms
            self.la.write_termination = '\x00'  # set termination character
            self.la.read_termination = '\x00'
        except pyvisa.VisaIOError as e:
            print("Problem while connecting to 7124: %s" % e)

        else:
            print("7124 is connected. Continue ...")

    def lock(self):
        self.la.write('LOCK')

    def aqn(self):
        self.la.write('AQN')
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def setOSC(self, mode):
        self.la.write('RCUOSC '+str(mode)+'\x00')
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def setFreq(self, freq):
        self.la.write('OF. '+str(freq))
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def setAmp(self, amp):
        self.la.write('OA. '+str(amp))
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def getData_Mag(self):
        try:
            self.la.write('MAG.')
#           time.sleep(0.0001)
            V_str = self.la.read()
            extrabit = self.la.read()
        except pyvisa.VisaIOError as e:
            print("Couldn't read values: %s" % e)
            print("Set V = 0")
            V_str = ['0', '0']
        if V_str:
            self.data = float(V_str)

        return self.data

    def getData_XY(self, itrmax, dt=0):
        #                print '\t... getting Vx and Vy ...'

        currtime_start = time.time()
        t_ = time.clock()

        itr = 0
        timestamp, Vx, Vy = npy.zeros(
            itrmax), npy.zeros(itrmax), npy.zeros(itrmax)
        self.data = [npy.zeros(itrmax), npy.zeros(itrmax), npy.zeros(itrmax)]

        for itr in tqdm(range(itrmax)):
            try:
                self.la.write('XY.')
                timestamp[itr] = currtime_start + (time.clock()-t_)
                V_str = self.la.read().split(',')
                extrabit = self.la.read()
            except pyvisa.VisaIOError as e:
                print("Couldn't read values: %s" % e)
                print("Set V = 0")

            if V_str:
                Vx[itr], Vy[itr] = float(V_str[0].strip(
                    '\x00')), float(V_str[1].strip('\x00'))

            time.sleep(dt)

        self.data = [timestamp, Vx, Vy]
        return self.data

    def setCurveBuffer(self, n=3):

        self.la.write('CBD ' + str(n))
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def setBufferMode(self, n=1):

        self.la.write('CMODE ' + str(n))
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def setLength(self, n):

        self.la.write('LEN ' + str(int(n)))
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def runCurve(self):

        self.la.write('TD')
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def dumpBuffer_XY(self, bufferlength):
        V_str_x = []
        V_str_y = []
        self.la.write('DC 0')

        while len(V_str_x) < bufferlength:

            V_str_x = npy.append(V_str_x, self.la.read().split('\n'))
#                print V_str_x, len(V_str_x)
        extrabit1 = self.la.read()
        self.la.write('DC 1')
        while len(V_str_y) < bufferlength:
            V_str_y = npy.append(V_str_y, self.la.read().split('\n'))
#                print V_str_y, len(V_str_y)
        extrabit1 = self.la.read()
        return V_str_x, V_str_y

    def initNewCurve(self):

        self.la.write('NC')
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def setStorageInterval(self, t):

        self.la.write('STR '+str(int(t)))
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()

    def getBufferStatus(self):

        self.la.write('M')
        status, nsweeps, statusbyte, npoints = self.la.read().split(',')
        extrabit1 = self.la.read()

        return status, nsweeps, statusbyte, npoints

    def setAQN(self):
        self.la.write('AQN')
        extrabit1 = self.la.read()
        extrabit2 = self.la.read()


class ls370(object):
    '''
    '''

    def __init__(self, address='13', gpib='GPIB1', **kwargs):
        try:
            print("Checking connection to 370 AC Resistance Bridge ...")
            # self.ac=instrument('GPIB1::'+address+'::INSTR',**kwargs)
            self.ac = rm.open_resource(gpib+'::'+address+'::INSTR', **kwargs)
        except pyvisa.VisaIOError as e:
            print("Problem while connecting to AC bridge LS370: %s" % e)
        else:
            print("AC bridge connected. Continue ...")

    def ScanChannel(self, channel, autoscan):
        self.ac.write('SCAN '+channel+","+autoscan)

    def setResRange(self, channel: str, mode: str, excitRange: str, resRange: str, autorange: str, csOff: str):
        """
        Sets Resistance and Excitation ranges, selects the mode and autorange 
        
        Parameters
        ----------
        channel: str
            Specifies which channel to configure: 1-16, 0 = all channels.
        mode: str
            0 = Voltage Excitation Mode, 1 = Current Excitation Mode.
        excitation: str
            Excitation range number: 1-22 for Current Excitation, 1-12 for Voltage Excitation.
        range: str
            Resistance range number: 1-22.
        autorange: str 0 = autorange off, 1 = autorange on.
        cs off: str
            0 = excitation on, 1 = excitation off. 
        """
        self.ac.write('RDGRNG '+channel+','+mode+','+excitRange +
                      ','+resRange+','+autorange+','+csOff+';*WAI')
    
    def setFilter(self, on: int, channel: str, setlT: int, wind: int):
        """ 
        Turns on/off the filter and sets settling time and window size
        
        Parameters
        ----------
        on: int
            1 for on and 0 for off
        channel: str
            The channel the filter is applied to
        setlT: int
            Defines the settling time
        wind: int
            Defines the window size (in %)
        """
        self.ac.write('FILTER '+channel+','+str(on)+','+str(setlT)+','+str(wind)+';*WAI')
    
    def checkFilter(self, channel: str):
        """
        Returns the status of the filter in the form nn,nnn,nn
        indicating on/off, settling time, window size
        """
        self.ac.write('FILTER? '+channel+';*WAI')
        time.sleep(0.1)
        res = 0
        try:
            res = self.ac.read()
        except:
            pass
        return res

    def getRes(self, itrmax, dt, channel):
        print('... getting R_RuO ...')
        itr = 0
        R = 0.0
        resistance = 0.0
        self.ScanChannel(ch=channel, autoscan='0')

        while itr < itrmax:
            self.ac.write('RDGR?'+str(channel)+';*WAI')
            resistance += float(self.ac.read())
            time.sleep(dt)
            itr += 1

        return float(resistance/itrmax)
    
    def acquire(self, Nscans: int, Tdelay: float, channel: int, scan: bool = True) -> float:
        """
        Scans Nscans number of points and returns the average, with Tdelay of delay between the scans
        
        Parameters:
        ----------
        Nscans: int
            Number of scans to average over
        Tdelay: int
            Delay between scans
        channel: int
            Specifies the channel
        scan: bool
            To optimize the amount of messages sent you can set this parameter to false
            if you are sure that the correct channel is selected at the time the function is called
            (e.g if only one channel is used and it has already been scanned once)
        """
        resistance = 0.
        if scan:
            self.ScanChannel(channel=str(channel),autoscan='0') #make sure that the channel is correct        
        
        for itr in range(Nscans):
            self.ac.write('RDGR?'+str('1')+';*WAI') 
            resistance+=float(self.ac.read())
            time.sleep(Tdelay)
            
        return float(resistance/Nscans)
      


class keithley6221(object):

    def __init__(self, address='10', **kwargs):
        try:
            print("Checking connection to AC current source")
            # self.K6221=instrument('GPIB1::'+address+'::INSTR',**kwargs)
            self.K6221 = rm.open_resource(
                'GPIB1::'+address+'::INSTR', **kwargs)
        except pyvisa.VisaIOError as e:
            print("Problem while connecting to Keithley 6221: %s" % e)
        else:
            print("AC source connected. Continue ...")

    def setDCcurrent(self, current):
        self.K6221.write('CLEar')
        self.K6221.write('CURRent:RANGe:AUTO ON')
        self.K6221.write('CURRent '+str(current))

    def ON(self):
        self.K6221.write('OUTPut ON')

    def OFF(self):
        self.K6221.write('OUTPut OFF')

    def configureSineWaveform(self, freq, current):
        f = str(freq)
        I = str(current)
        self.K6221.write('SOUR:WAVE:FUNC SIN')
        self.K6221.write('SOUR:WAVE:FREQ ' + f)
        self.K6221.write('SOUR:WAVE:AMPL ' + I)
    #        self.K6221.write('SOUR:WAVE:RANG BEST')

    def turnOnWave(self):
        print('... setting ac current ...')
        self.K6221.write('SOUR:WAVE:ARM')
        self.K6221.write('SOUR:WAVE:INIT')

    def turnOffWave(self):
        self.K6221.write('SOUR:WAVE:ABOR')

    def __del__(self):
        if hasattr(self, 'K6221') and self.K6221:
            self.K6221.close()


class keithley6221_2(object):
    '''
    '''

    def __init__(self, address='10', **kwargs):
        try:
            print("Checking connection to AC current source")
            # self.K6221=instrument('GPIB1::'+address+'::INSTR',**kwargs)
            self.K6221 = rm.open_resource(
                'GPIB1::'+address+'::INSTR', **kwargs)
        except pyvisa.VisaIOError as e:
            print("Problem while connecting to Keithley 6221: %s" % e)
        else:
            print("AC source connected. Continue ...")

    def setDCcurrent(self, current):
        self.K6221.write('CLEar')
        self.K6221.write('CURRent:RANGe:AUTO ON')
        self.K6221.write('CURRent '+str(current))

    def ON(self):
        self.K6221.write('OUTPut ON')

    def OFF(self):
        self.K6221.write('OUTPut OFF')

    def configureSineWaveform(self, freq, current):
        f = str(freq)
        I = str(current)
        self.K6221.write('SOUR:WAVE:FUNC SIN')
        self.K6221.write('SOUR:WAVE:FREQ ' + f)
        self.K6221.write('SOUR:WAVE:AMPL ' + I)
#        self.K6221.write('SOUR:WAVE:RANG BEST')

    def turnOnWave(self):
        self.K6221.write('SOUR:WAVE:ARM')
        self.K6221.write('SOUR:WAVE:INIT')

    def turnOffWave(self):
        self.K6221.write('SOUR:WAVE:ABOR')


class EGG7260(object):
    '''
'''
    def __init__(self, gpib_address='13', **kwargs):
        try:
            print("Checking connection to 7260 ...")
            # self.la=instrument('GPIB1::'+gpib_address+'::INSTR',**kwargs)
            self.la = rm.open_resource('GPIB1::'+gpib_address+'::INSTR', **kwargs)
        except pyvisa.VisaIOError as e:
            print("Problem while connecting to 7260: %s" % e)
        else:
            print("7260 is connected. Continue ...")
            
    def lock(self):
        self.la.write('LOCK')

    def aqn(self):
        self.la.write('AQN')

    def setFreq(self, freq):
        self.la.write('OF. '+str(freq))

    def setAmp(self, amp):
        self.la.write('OA. '+str(amp))

    def getData_XY(self, itrmax, dt):
        print ('... getting Vx and Vy ...')

        itr = 0
        Vx, Vy = npy.zeros(itrmax), npy.zeros(itrmax)
        self.data = [npy.zeros(itrmax), npy.zeros(itrmax)]

        while itr < itrmax:
            V_str = self.la.ask('XY.').split(',')
            if V_str:
                Vx[itr], Vy[itr] = float(V_str[0].strip(
                    '\x00')), float(V_str[1].strip('\x00'))

            time.sleep(dt)
            itr += 1

        self.data = [Vx, Vy]
        return self.data
    
    def getData(self):
        V_str = self.la.query('XY.').split(',')
        if V_str:
            Vx,Vy = float(V_str[0].strip('\x00')), float(V_str[1].strip('\x00\x00\r\n'))
            self.data = npy.append(Vx,Vy)

        return self.data
    
    def getData_3(self, itrmax):
        Vx, Vy, phase = 0., 0., 0.
        Vx_sum, Vy_sum , phase_sum = 0., 0., 0.
        itr_max = itrmax
        for i in range(0,itr_max):
            V_str = self.la.query('XY.').split(',')
            Phase_str = self.la.query('PHA.')
            if V_str:
                Vx,Vy,phase = float(V_str[0].strip('\x00')), float(V_str[1].strip('\x00\x00\r\n')),float(Phase_str.strip('\x00\r\n')) #
                Vx_sum = Vx_sum + Vx
                Vy_sum = Vy_sum + Vy
                phase_sum = phase_sum + phase
            #tm.sleep(0.01)
        self.data = [Vx_sum/itr_max, Vy_sum/itr_max, phase_sum/itr_max]
        
        return self.data

    def setAQN(self):
        self.la.write('AQN')

    def startParam(self):
        self.la.write('IE 0')
        self.la.write('VMODE 3')
        self.la.write('FET 1')
        self.la.write('FLOAT 1')
        self.la.write('LF 0')
        self.la.write('OA. 0.000')
        self.la.write('TC 13')

    def __del__(self):
        if hasattr(self, 'la') and self.la:
            self.la.close()
            
    ### added more controls ###
    #1: Signal Channel
    def setIMODE(self, n):
        """
        The value of n sets the input mode according to the following table:
        n Input mode
        0 Current mode off - voltage mode input enabled
        1 High bandwidth (HB) current mode enabled - connect signal to B input connector
        2 Low noise (LN) current mode enabled - connect signal to B input connector
        If n = 0 then the input configuration is determined by the VMODE command.
        If n > 0 then current mode is enabled irrespective of the VMODE setting.
        """
        self.la.write('IMODE '+ str(n))
    
    def setVMODE(self, n):
        """
        Voltage input configuration
        The value of n sets up the input configuration according to the following table:
        n Input configuration
        0 Both inputs grounded (test mode)
        1 A input only
        2 -B input only
        3 A-B differential mode
        Note that the IMODE command takes precedence over the VMODE command.
        """
        self.la.write('VMODE ' + str(n))
        
    def setFET(self, n):
        """
        Voltage mode input device control
        The value of n selects the input device according to the following table:
        n Selection
        0 Bipolar device, 10 kΩ input impedance, 2 nV/√Hz voltage noise at 1 kHz
        1 FET, 10 MΩ input impedance, 5 nV/√Hz voltage noise at 1 kHz
        """
        self.la.write('FET ' + str(n))
    
    def setFLOAT(self, n):
        """
        Input connector shield float/ground control
        The value of n sets the input connector shield switch according to the following table:
        n Selection
        0 Ground
        1 Float (connected to ground via a 1 kΩ resistor)
        """
        self.la.write('FLOAT ' + str(n))
        
    def setCP(self, n):
        """
        Input connector shield float/ground control
        The value of n sets the input coupling mode according to the following table:
        n Coupling mode
        0 AC
        1 DC
        """
        self.la.write('CP ' + str(n))
    
    def setSEN(self, n):
        """
        Full-scale sensitivity control
        The value of n sets the full-scale sensitivity according to the following table,
        depending on the setting of the IMODE control:
        
        n   IMODE=0   IMODE=1    IMODE=2
        1   2 nV      2 fA       n/a
        2   5 nV      5 fA       n/a
        3   10 nV     10 fA      n/a
        4   20 nV     20 fA      n/a
        5   50 nV     50 fA      n/a
        6   100 nV    100 fA     n/a
        7   200 nV    200 fA     2 fA
        8   500 nV    500 fA     5 fA
        9   1 µV      1 pA       10 fA
        10  2 µV     2 pA        20 fA
        11  5 µV     5 pA        50 fA
        12  10 µV    10 pA       100 fA
        13  20 µV    20 pA       200 fA
        14  50 µV    50 pA       500 fA
        15  100 µV   100 pA      1 pA
        16  200 µV   200 pA      2 pA
        17  500 µV   500 pA      5 pA
        18  1 mV     1 nA        10 pA
        19  2 mV     2 nA        20 pA
        20  5 mV     5 nA        50 pA
        21  10 mV    10 nA       100 pA
        22  20 mV    20 nA       200 pA
        23  50 mV    50 nA       500 pA
        24  100 mV   100 nA      1 nA
        25  200 mV   200 nA      2 nA
        26  500 mV   500 nA      5 nA
        27  1 V      1 µA        10 nA
        
        Floating point mode can only be used for reading the sensitivity, which is reported in
        volts or amps. For example, if IMODE = 0 and the sensitivity is 1 mV the command
        SEN would report 18 and the command SEN. would report +1.0E-03. If IMODE was
        changed to 1, SEN would still report 18 but SEN. would report +1.0E-09.
        """
        self.la.write('SEN ' + str(n))
    
    def setSEN_full(self):
        """
        full-scale sensitivity
        """
        self.la.write('SEN.')
    
    def setAS(self):
        """
        Perform an Auto-Sensitivity operation
        The instrument adjusts its full-scale sensitivity so that the magnitude output lies
        between 30 % and 90 % of full-scale.
        """
        self.la.write('AS')
        
    def setASM(self):
        """
        Perform an Auto-Measure operation
        The instrument adjusts its full-scale sensitivity so that the magnitude output lies
        between 30 % and 90 % of full-scale, and then performs an auto-phase operation to
        maximize the X channel output and minimize the Y channel output.
        """
        self.la.write('ASM')
    
    def setACGAIN(self, n):
        """
        AC Gain control
        Sets the gain of the signal channel amplifier. Values of n from 0 to 9 can be entered,
        corresponding to the range 0 dB to 90 dB in 10 dB steps.
        """
        self.write('ACGAIN ' + str(n))
    
    def setAUTOMATIC(self, n):
        """
        AC Gain automatic control
        The value of n sets the status of the AC Gain control according to the following table:
        
        n Status
        0 AC Gain is under manual control, either using the front panel or the ACGAIN command
        1 Automatic AC Gain control is activated, with the gain being adjusted according
            to the full-scale sensitivity setting
        """
        self.la.write('AUTOMATIC ' + str(n))
    
    def setLF(self, n):
        """
        Signal channel line frequency rejection filter control
        n Selection
        0 Off
        1 Enable 50 or 60 Hz notch filter
        2 Enable 100 or 120 Hz notch filter
        3 Enable both filters
        """
        self.la.write('LF' + str(n))
        
    def setLINE50(self, n):
        """
        Signal channel line frequency rejection filter center frequency control
        The value of n sets the line frequency notch filter center frequency according to the
        following table:
        n Notch filter mode
        0 60 Hz (and/or 120 Hz)
        1 50 Hz (and/or 100 Hz)
        """
        self.la.write('LINE50 ' + str(n))

        # print(self.la.query("*STB?"))
        
    def setSAMPLE(self, n):
        """
        Main analog to digital converter sample rate control
        The sampling rate of the main analog to digital converter, which is nominally
        166 kHz, may be adjusted from this value to avoid problems caused by the aliasing of
        interfering signals into the output passband.
        n may be set to 0, 1, 2 or 3, corresponding to four different sampling rates (not
        specified) near 166 kHz.
        """
        self.la.write('SAMPLE ' + str(n))
    
    def setRANGE(self, n):
        """
        Signal Recovery/Vector Voltmeter mode selector
        The value of n sets the operating mode of the instrument as follows:
        n Mode
        0 Signal Recovery
        1 Vector Voltmeter
        NOTE: Instrument always reverts to signal recovery mode (n=0) on power-up.
        """
        self.la.write('RANGE ' + str(n))
        
class magnet_9T(object):
    '''
    '''

    def __init__(self, ip_address='10.0.0.9', **kwargs):
        try:
            print ("Checking connection to 9 T magnet ...")
            # self.magnet = instrument(
            #     'TCPIP0::'+ip_address+'::7180::SOCKET', term_chars='\x0D\x0A', send_end=True, **kwargs)
            self.magnet = rm.open_resource('TCPIP0::'+ip_address+'::7180::SOCKET', **kwargs)
            self.magnet.write_termination = '\x0D\x0A'
            self.magnet.read_termination = '\x0D\x0A'
            self.magnet.read()
            self.magnet.read()
        except pyvisa.VisaIOError as e:
            print ("Problem while connecting to 9 T magnet: %s" % e)
        else:
            print ("9 T magnet is connected. Continue ...")

    def currentTarget(self, current):
        '''
        Sets the target current, [A]
        '''
        print ('\t<Target current %f>' % current)
        self.magnet.write('CONF:CURR:TARG '+str(current))

    def ramp_rate_units(self, units):
        self.magnet.write('CONF:RAMP:RATE:UNITS '+str(units))

    def segments(self, num, ramptime, units):
        print ('... setting ramp segments ...')
        maxfield = 89.37  # [A]

        if units == 0:
            un = '[A/sec]'
            maxramprate = 0.122
        else:
            un = '[A/min]'
            maxramprate = 7.32

        self.ramp_rate_units(units)
        time.sleep(0.1)
        self.magnet.write('CONF:RAMP:RATE:SEG '+str(num))
        time.sleep(0.1)
        for i in range(1, num+1):
            up_current_bound = maxfield/2**abs(i-num)
            ramp_rate_segment = (maxfield/2**abs(i-num-1))/ramptime

            if ramp_rate_segment > maxramprate:
                print ('Ramp rate %f exceeds maximum value %f' % (ramp_rate_segment, maxramprate))
                time.sleep(1.)
                sys.exit(1)

            self.magnet.write('CONF:RAMP:RATE:CURR '+str(i)+',' +
                              str(ramp_rate_segment)+','+str(up_current_bound))
            print ('Segment %i up to %f [A] with ramp rate %f %s' % (i, up_current_bound, ramp_rate_segment, un))
            time.sleep(0.1)

    def fieldTarget(self, field):
        '''
        Sets the target field in kG or T
        '''

        self.magnet.write('CONF:FIELD:TARG '+str(field))

    def pauseProgrammer(self):
        self.magnet.write('PAUSE')

    def rampMode(self):
        # print '\t... ramping ...'
        self.magnet.write('RAMP')

    def zero(self):
        self.magnet.write('ZERO')

    def pswitch(self, state):
        self.magnet.write('PSwitch '+state)

    def fieldValue(self):
        H = self.magnet.ask('FIELD:MAG?\x0A\x0D')

        return float(H)

    def currentValue(self):
        I = self.magnet.ask('CURR:MAG?\x0A\x0D')

        return float(I)

    def status(self):
        return str(self.magnet.ask('STATE?\x0A\x0D'))

    def __del__(self):
        if hasattr(self, 'magnet') and self.magnet:
            self.magnet.close()


class keithley2200(object):
    '''
    '''

    def __init__(self, address='24', **kwargs):
        try:
            print ("Checking connection to DC current source")
            # self.DC = instrument('GPIB1::'+address+'::INSTR', **kwargs)
            self.DC = rm.open_resource('GPIB1::'+address+'::INSTR', **kwargs)
        except pyvisa.VisaIOError as e:
            print ("Problem while connecting to Keithley 2200: %s" % e)
        else:
            print ("DC source connected. Continue ...")

    def setDCcurrent(self, current):
        self.DC.write('CLEar')
        self.DC.write('CURRent:RANGe:AUTO ON')
        self.DC.write('CURRent '+str(current))

    def getDCvoltage(self):
        voltage = self.DC.ask('FETCh:VOLTage:DC?')
        try:
            voltage = float(voltage)
        except:
            voltage = -1.0
        return voltage

    def setDCvoltage(self, volts):
        self.DC.write('VOLTage ' + str(volts)+'V')

    def ON(self):
        self.DC.write('OUTPut ON')

    def OFF(self):
        self.DC.write('OUTPut OFF')

from qcodes.instrument_drivers.yokogawa import YokogawaGS200

class GS200(object):
    def __init__(self,address='TCPIP0::128.131.126.38::inst0::INSTR'):
        #'USB0::0x0B21::0x0039::90Y412705::INSTR'
        try:
            print('Checking connection to GS200 Yokogawa DC voltage/Current source')
            self.gs = YokogawaGS200("GS200", address=address, terminator="\n")
        except pyvisa.VisaIOError:
            print('Something went wrong, no connection')
        else:
            print('All good. GS200 connected. Please continue')
        
    def SetCurrent(self,Curr):
        try:
            self.gs.current(Curr)
        except ValueError:
            print('Have you set the mode in current first?')

    def SetMode(self,mode):
        self.gs.source_mode(mode)
        print('Set to mode',self.gs.source_mode())

    def ON(self):
        self.gs.output('on')

    def OFF(self):
        self.gs.output('off')

    def SetVoltage(self,Volt):
        try:
            self.gs.voltage(Volt)
        except ValueError:
            print('Have you set the mode in voltage first?')
        
    def SetAutoRange(self,ok=False):
        self.gs.auto_range(ok)

    def SetCurrentRange(self,Range):
        try:
            self.gs.current_range(Range)
        except ValueError:
            print('Have you set the mode in current first?')

    def SetVoltageRange(self,Range):
        try:
            self.gs.voltage_range(Range)
        except ValueError:
            print('Have you set the mode in voltage first?')
        
                
    def RampCurr(self,Curr0,to,step,tstep):
        self.gs.current(Curr0)
        self.gs.ramp_current(to,step,tstep)

    def GetCurrent(self):
        try:
            return(self.gs.current())
        except ValueError:
            print('Have you set the mode in current first?')
            return(None)

    def GetVoltage(self):
        try:
            return(self.gs.voltage())
        except ValueError:
            print('Have you set the mode in voltage first?')
            return(None)

    def STOP(self):
        self.gs.output('off')
        self.gs.close()

class Picoscope(object):
    def __init__(self):
        from picoscope import ps5000a
        try:
            self.la = ps5000a.PS5000a()
        except Exception :
            print('Problem connection to picoscope')
            
    def MeasParam(self,ch,mode='DC',r=10, en=True,BWLim=False):
        self.la.setChannel(ch, mode, r, enabled=en, BWLimited=BWLim)
        print('channel %s is %s' %(ch,en))

    def getData(self,ch,frqc,nsamples,resolution='16'):
        data = {}
        data["Channel_"+ ch] = npy.zeros(nsamples, dtype=npy.float64)
        self.la.setSamplingFrequency(frqc, nsamples) # frqc= [samples/s]
        self.la.setResolution(resolution)#Number of bits
        self.la.runBlock()
        while(self.la.isReady() is False):
            time.sleep(0.01)

        self.la.getDataV(ch, numSamples = nsamples, dataV = data["Channel_"+ ch])
        return(data["Channel_"+ ch])
        
    def close(self):
        self.la.close()
        print("Picoscope closed")


import nidaqmx
from nidaqmx.system import System
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE

class NI_USB6211:
    
    def __init__(self, device_name="Dev1"):
        
        system = System.local()
        if device_name not in system.devices:
            print("ERROR: Device not found. Check any spelling errors")
        else:
            print(f"Device {device_name} connected, continue...")
            self.device_name = device_name
    
    def acquire(self, channel: str, minv: float = -5.0, maxv: float = 5.0):
        """Adds an analog input channel to a task, configures the range, and reads data
        
        Arguments:
        ---------
        channel (str): Specifies the channel
        minv (Optional[float]): Specifies in Volts the
                minimum value you expect to measure.
        maxv (Optional[float]): Specifies in Volts the
                maximum value you expect to measure.
        """
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.device_name+"/"+channel, min_val=minv, max_val=maxv)
            return task.read()
    
    def acquire_n(self, rate: float, channel: str, samps_n: int, minv: float = -5.0, maxv: float = 5.0):
        """Acquires finite amount of data using hardware timing
        
        Arguments:
        ---------
        rate (float): Specifies the sampling rate in samples per
                channel per second. If you use an external source for
                the Sample Clock, set this input to the maximum expected
                rate of that clock.
        channel (str): Specifies the channel
        samps_n (int): Specifies the number of
                samples to acquire or generate for each channel in the
                task, returns an error if the specified value is negative.
        minv (Optional[float]): Specifies in Volts the
                minimum value you expect to measure.
        maxv (Optional[float]): Specifies in Volts the
                maximum value you expect to measure.
        
        """
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.device_name+"/"+channel, min_val=minv, max_val=maxv)
            task.timing.cfg_samp_clk_timing(rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samps_n)
            data = task.read(READ_ALL_AVAILABLE)
            # print("Acquired data: [" + ", ".join(f"{value:f}" for value in data) + "]")
            return data
    
    def acquire_excit(self, rate: float, samps_n: int, channel: str, minv: float = -5.0, maxv: float = 5.0, voltage_excit_val: float=0.0):
        """Adds an analog input channel to a task and supplies excitation to the sensor, configures the range, and reads data
        
        Arguments:
        ---------
        rate (float): Specifies the sampling rate in samples per
                channel per second. If you use an external source for
                the Sample Clock, set this input to the maximum expected
                rate of that clock.
        samps_n (int): Specifies the number of
                samples to acquire or generate for each channel in the task,
                returns an error if the specified value is negative.
        channel (str): Specifies the channel
        minv (Optional[float]): Specifies in Volts the
                minimum value you expect to measure.
        maxv (Optional[float]): Specifies in Volts the
                maximum value you expect to measure.
        voltage_excit_val (Optional[float]): Specifies in volts the
                amount of excitation supplied to the sensor. Refer to
                the sensor documentation to determine appropriate
                excitation values.
        """
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan_with_excit(self.device_name+"/"+channel, min_val=minv, max_val=maxv, voltage_excit_val=voltage_excit_val)
            task.timing.cfg_samp_clk_timing(rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samps_n)
            data = task.read(READ_ALL_AVAILABLE)
            # print("Acquired data: [" + ", ".join(f"{value:f}" for value in data) + "]")
            return data
        
    #TODO 2 channels in parallel
    def acquire_2chan_n(self, channel1: str, channel2: str, minv1: float, maxv1: float, minv2: float, maxv2: float, rate: float, samps_n: int):
        """
        Adds multiple analog input channels to a task, configures their range, and reads all data in range
        
        Arguments:
        ---------
        channel[i] (str): Specifies the channel i
        minv[i] (Optional[float]): Specifies in Volts the
                minimum value you expect to measure. (for channel i)
        maxv[i] (Optional[float]): Specifies in Volts the
                maximum value you expect to measure. (for channel i)
        rate (float): Specifies the sampling rate in samples per
            channel per second. If you use an external source for
            the Sample Clock, set this input to the maximum expected
            rate of that clock.
        samps_n (int): Specifies the number of
                samples to acquire or generate for each channel in the task,
                returns an error if the specified value is negative.
        """
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan_with_excit(self.device_name+"/"+channel1, min_val=minv1, max_val=maxv1)
            task.ai_channels.add_ai_voltage_chan_with_excit(self.device_name+"/"+channel2, min_val=minv2, max_val=maxv2)
            task.timing.cfg_samp_clk_timing(rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samps_n)
            data = task.read(READ_ALL_AVAILABLE)
            # print("Acquired data: [" + ", ".join(f"{value:f}" for value in data) + "]")
            return data