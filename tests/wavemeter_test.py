import ctypes
import traceback
import time
import numpy as np
import serial
from pcaspy import SimpleServer, Driver
import threading
import os
#from epics import caput
#os.environ['EPICS_CA_ADDR_LIST']='192.168.1.157'
#os.environ['EPICS_CA_ADDR_LIST']='10.29.119.90'
#os.environ['EPICS_CA_ADDR_LIST']='10.54.0.1'
#os.environ['EPICS_CA_ADDR_LIST']='192.168.1.1'

prefix = "LaserLab:"
pvdb = {
        'wavenumber_1': {"type":"string", "units":"wavenumber"},
        'wavenumber_2': {"type":"string", "units":"wavenumber"},
        'wavenumber_3': {"type":"string", "units":"wavenumber"},
        'wavenumber_4': {"type":"string", "units":"wavenumber"}
        }

class HighFinnesse(Driver):
    def __init__(self):
        super(HighFinnesse,self).__init__()

        self.mapping = {
                        "calibrate_wavemeter":self.calibrate
                        }
        self.run = True
        self.refresh_time = 10
        self.tid =  threading.Thread(target = self.read_from_device)
        self.tid.setDaemon(True)
        self.connect_to_device()

    def connect_to_device(self):

        try:
            print("connecting")
            # Load the .dll file
            self.wlmdata = ctypes.WinDLL("c:\\windows\\system32\\wlmData.dll")

            # Specify required argument types and return types for function calls
            self.wlmdata.GetFrequencyNum.argtypes = [ctypes.c_long, ctypes.c_double]
            self.wlmdata.GetFrequencyNum.restype  = ctypes.c_double

            # self.wlmdata.GetLinewidth.argtypes = [ctypes.c_long, ctypes.c_double]
            # self.wlmdata.GetLinewidth.restype  = ctypes.c_double

            self.wlmdata.GetExposureNum.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
            self.wlmdata.GetExposureNum.restype  = ctypes.c_long
            self.wlmdata.Calibration.argtypes = [ctypes.c_long, ctypes.c_long,
                                    ctypes.c_double, ctypes.c_long]
            self.wlmdata.Calibration.restype  = ctypes.c_long

            self.wlmdata.Operation.argtypes = [ctypes.c_int]
            self.wlmdata.Operation.restype  = ctypes.c_long

        except:
            raise Exception('Failed to connect to wavemeter\n',traceback.format_exc())

        wavenumber_1 = self.wlmdata.GetFrequencyNum(1,0) / 0.0299792458
        wavenumber_2 = self.wlmdata.GetFrequencyNum(2,0) / 0.0299792458
        wavenumber_3 = self.wlmdata.GetFrequencyNum(3,0) / 0.0299792458
        wavenumber_4 = self.wlmdata.GetFrequencyNum(4,0) / 0.0299792458

        try:

            self.setParam('wavenumber_1',""+str(wavenumber_1))
            self.setParam('wavenumber_2',""+str(wavenumber_2))
            self.setParam('wavenumber_3',""+str(wavenumber_3))
            self.setParam('wavenumber_4',""+str(wavenumber_4))
            self.updatePVs()

            #print("successful connection to the mS^2")
            self.tid.start()
        except Exception as e:
            print(e)


    def read_from_device(self):
        while self.run:
            wavenumber_1 = self.wlmdata.GetFrequencyNum(1,0) / 0.0299792458
            wavenumber_2 = self.wlmdata.GetFrequencyNum(2,0) / 0.0299792458
            wavenumber_3 = self.wlmdata.GetFrequencyNum(3,0) / 0.0299792458
            wavenumber_4 = self.wlmdata.GetFrequencyNum(4,0) / 0.0299792458

            #time.sleep(0.001*self.refresh_time)

            # expos_11 = self.wlmdata.GetExposureNum(1,1,0)
            # expos_12 = self.wlmdata.GetExposureNum(1,2,0)
            # expos_21 = self.wlmdata.GetExposureNum(2,1,0)
            # expos_22 = self.wlmdata.GetExposureNum(2,2,0)
            # print(self.wlmdata.GetLinewidth(2,0))

            data = [wavenumber_1,wavenumber_2, wavenumber_3, wavenumber_4]
            try :
                self.setParam('wavenumber_1',""+str(wavenumber_1))
                self.setParam('wavenumber_2',""+str(wavenumber_2))
                self.setParam('wavenumber_3',""+str(wavenumber_3))
                self.setParam('wavenumber_4',""+str(wavenumber_4))
                self.updatePVs();
                #caput('wavenumber_1',""+str(wavenumber_1))
                #caput('wavenumber_2',""+str(wavenumber_2))
                #caput('wavenumber_3',""+str(wavenumber_3))
                #caput('wavenumber_4',""+str(wavenumber_4))

            except Exception as e:
                print(e)



    def calibrate(self,args):
        self.wlmdata.Operation(0) # stop
        self.wlmdata.Calibration(2,2,384.22811520332100,2) #calibrate
        self.wlmdata.Operation(2) #start


if __name__ == "__main__":
    server = SimpleServer()
    server.createPV(prefix,pvdb)
    driver = HighFinnesse()
    print("started")
    while True:
        #this variable can change the speed of how oftein in updatePVs
        server.process(.01)
