
import os
import sys
# Setup paths
this_path = os.path.abspath(__file__)
father_path = os.path.abspath(os.path.join(this_path, "../../"))
print(father_path)
sys.path.append(father_path)
# if we have to hardcode sth, it might as well be at the top of the file
# these are the channels ON the tagger that each magnetof is connected to
MAGNETOF_1_CHANNEL = 3
MAGNETOF_2_CHANNEL = 1
SAVE_FILE_FOLDER = r'T:\\RAPTOR\\DAQ\\scans\\'

import sys
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QFileDialog
import pyqtgraph as pg
import pandas as pd
import numpy as np
from tagger import Tagger
from scripts.GatePlotWidget import *
#import tagger # keep it here, to include the drivers boolean with the tagger namespace
import time
from datetime import datetime
import threading as th
from math import ceil, floor

from CaChannel.util import caget
from pcaspy import Driver, SimpleServer
import epics


prefix = 'LaserLab:'

max_events = 10**3
pvdb = {
        'Counts'         :     {'type':'int', 'value':0},
        'Counts_sum'     :     {'type':'int', 'value':0},
        'NoOfBins'       :     {'type':'int', 'value':400},
        'dt'             :     {'prec':3,'unit':'us','value':0},
        'Hist'           :     {'count': 3*max_events,'type' : 'int'},
        'Clear'          :     {'type':'enum', 'enums':['NoReset','Reset']},
       }


class RaptorEPICSDriver(Driver):
    def __init__(self):
        Driver.__init__(self)

    def write(self, reason, value):
        self.setParam(reason,value)
        self.updatePVs()



class Acquisition(QtWidgets.QMainWindow):
    def __init__(self):
        super(Acquisition, self).__init__()
        uic.loadUi('C:\\Users\\EMALAB\\Desktop\\TW_DAQ\\src\\ui\\files\\acquisition.ui', self)
        self.running = True

        self.make_epics_driver()

        self.list_data = []
        self.data = []
        self.wavenumber = 0
        self.initial_max_wvn_recorded = 1
        self.initial_min_wvn_recorded = 1000000
        self.max_wvn_recorded = self.initial_max_wvn_recorded # for binning
        self.min_wvn_recorded = self.initial_min_wvn_recorded
        self.spectrum_x_vals = []
        self.spectrum_y_vals = []
        self.record_file = None
        self.file_name = None
        #
        self.rates = []
        self.freqs = []
        self.time_plot_bins = []
        self.rate = 0
        self.prev = time.time()
        # self.is_magnetof_1_biased = self.check_if_magnetof_is_biased(magnetof=1, bias=1000)
        # self.is_magnetof_2_biased = self.check_if_magnetof_is_biased(magnetof=2, bias=1000)

        #
        self.bin_size_cm = self.wavenumber_bin.value() * 0.0000334 # convert binsize from MHz to inverse cm
        self.spectrum_bins = np.linspace(self.min_wvn_recorded, self.max_wvn_recorded, int( abs(self.max_wvn_recorded - self.min_wvn_recorded) / 3 )) # initially create just 3 bins as a dummy, no need for more
        self.tdc_bins = np.linspace(self.tdc_start.value(),self.tdc_stop.value(),int((self.tdc_stop.value()-self.tdc_start.value())/self.tdc_bin.value()))


        self.hist = np.zeros(len(self.tdc_bins)-1)

        #self.connect_to_tdc()

        # self.gridlayout.addWidget(self.tofPlot,1,0,1,6)

        self.tofPlot.plotwidget.setTitle('TOF spectrum')
        self.timePlot.setTitle('Rate plot')

        self.tofPlot.new_gate.connect(self.flag_rebin)
        self.timeplot_rebin = True# was False. Changed by MAK on Febr 25 2022 for testing
        self.spectrum_rebin = True # this affects only the spectrum plot

        self.clearButton.clicked.connect(self.clear_data)
        self.tdc_start.valueChanged.connect(self.update_tdc_window)
        self.tdc_stop.valueChanged.connect(self.update_tdc_window)
        self.tdc_trig.valueChanged.connect(self.update_tdc_trig)
        self.wavenumber_bin.valueChanged.connect(self.update_spectrum_binsize)
        self.tdc_bin.valueChanged.connect(self.update_tof_binsize)
        self.recordBox.stateChanged.connect(self.record_box_state_changed)

        self.clear_data()

        self.calcTimer = QtCore.QTimer()
        self.calcTimer.timeout.connect(self.calc_rates)
        self.calcTimer.setInterval(50)
        self.calcTimer.start()

        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.update)
        self.updateTimer.setInterval(200)
        self.updateTimer.start()

        # self.taggerThread = th.Thread(target = self.read_tagger)
        # self.taggerThread.setDaemon(True)
        # self.taggerThread.start()

        self.wavenumberTimer = QtCore.QTimer()
        self.wavenumberTimer.timeout.connect(self.read_wavenumber)
        self.wavenumberTimer.setInterval(10)
        self.wavenumberTimer.start()

        self.clearTimer = QtCore.QTimer()
        self.clearTimer.timeout.connect(self.clear_data)
        self.clearTimer.setInterval(100000)
        self.clearTimer.start()

        self.scanning_rf = False


        self.show()

    def make_epics_driver(self):
        self.server = SimpleServer()
        self.server.createPV(prefix, pvdb)
        self.driver = RaptorEPICSDriver()

    def connect_to_tdc(self):
        self.tagger = Tagger()
        for i in range(0,4):
            self.tagger.enable_channel(i)
            self.tagger.set_channel_level(i,-0.85 )
            self.tagger.set_channel_falling(i)
            self.tagger.set_channel_window(i,start = int(self.tdc_start.value()*2000),stop = self.tdc_stop.value()*2000) # 1000*2000 is 1 ms after trig
            
        self.tagger.set_trigger_level(0.1)
        self.tagger.set_trigger_rising()
        self.tagger.start_reading()

    def update_tdc_window(self):
        self.tagger.stop_reading()

        for i in range(0,4):
            self.tagger.set_channel_window(i,start = int(self.tdc_start.value()*2000),stop = self.tdc_stop.value()*2000) # 1000*2000 is 1 ms after trig

        self.clear_data()
        self.tagger.start_reading()

    def update_tdc_trig(self):
        self.tagger.stop_reading()

        if abs(self.tdc_trig.value()) < 0.01:
            return

        for i in range(0,4):
            self.tagger.set_channel_level(i,self.tdc_trig.value())
            if self.tdc_trig.value()<=0:
                self.tagger.set_channel_falling(i)
            else:
                self.tagger.set_channel_rising(i)

        self.tagger.start_reading()

    def read_wavenumber(self):
        #self.wavenumber = caget('LaserLab:Wavemeter2:Wavenumber3')
        self.wavenumber = caget('LaserLab:wavenumber_3')

    def read_tagger(self):
        while self.running:   
            data = self.tagger.get_data()
            if data is not None:
                if not data == 0:
                    # data is a list of lists, where each sublist (dataline) is of the form ['bunch_no', 'events_per_bunch', 'channel', 'delta_t']
                    # it must be remembered that bunch_no is basically a useless number, it is just a counter of how many times the computer has 
                    # requested data from tha tagger. Not really useful, but styaing there for legacy.
                    # That is actually not true, it is the trigger number, counted by the DAQ card. So it is truly the bunch number. - Ruben
                    #data = np.row_stack(data)
                    t = [time.time()]*len(data)
                    wn = [self.wavenumber]*len(data)
                    data = np.column_stack([t,wn,data])

                    self.list_data.append(data)
                    try:
                        if self.recordBox.isChecked():
                            np.savetxt(self.record_file, X=data, delimiter=',')
                    except Exception as e:
                        print('couldnt save line')
                        print(e)

            time.sleep(0.0005)

    def flag_rebin(self):
        self.timeplot_rebin = True

    def update(self):
        if self.driver.getParam('Clear') == 1:
            self.clear_data()
            # self.driver.setParam('Clear',0)

        # TOF PLOT
        self.tofPlot.curve.setData(self.tdc_bins,self.hist, pen='r', stepMode=True)
        
        # SPECTRUM PLOT
        if self.data is not None and len(self.data)>1:
            try:
                # not this # self.freqPlot.plot(self.freqs,self.rates, clear=True, pen='r')
                # self.freqPlot.plot(self.spectrum_x_vals,self.spectrum_y_vals, clear=True, pen='r')
                pass
            except Exception as e:
                print(e)
                pass

        # TIME-EVOLUTION PLOT
        self.timePlot.plot(range(len(self.rates)), self.rates, clear=True, pen='b',symbol='o', stepMode=False)
        # NOT this # self.timePlot.plot(self.time_plot_bins, self.rates, clear=True, pen='b',symbol='o', stepMode=False)

        
    def scan_rf_loop(self):
        if self.scanning_rf:
            if time.time() - self.last_time > self.dt:
                counts = self.getCounts()
                if self.ref:
                    if self.RFCheck.isChecked():
                        self.counts_on.append(counts)
                        self.freq_on.append(self.range[self.index])

                        self.rf.toggle_state(False)
                        self.RFCheck.setChecked(False)

                    else:
                        self.counts_off.append(counts)
                        self.freq_off.append(self.range[self.index])

                        self.index += 1
                        self.rf.toggle_state(True)
                        self.RFCheck.setChecked(True)
                else:
                    self.counts_on.append(counts)
                    self.freq_on.append(self.range[self.index])

                    self.index += 1


                if self.index == len(self.range):
                    self.index = 0

                self.rf.set_freq(self.range[self.index])
                self.updateFreq(self.range[self.index])
                self.last_time = time.time()

                np.savetxt('data_on{}.csv'.format(self.scannr), np.column_stack((self.freq_on,self.counts_on)))
                np.savetxt('data_off{}.csv'.format(self.scannr), np.column_stack((self.freq_off,self.counts_off)))


    def calc_rates(self):
        T = time.time()
        if len(self.list_data) > 0:
            new_data = np.row_stack(self.list_data)
            if self.data is not None:
                self.data = np.concatenate([self.data, new_data])
            else:
                self.data = new_data
            # clean the self.list_data
            del self.list_data
            self.list_data = []
            data = self.data


            # CHANNEL INTERLOCK. If a magnetof is NOT biased then we do not include the data from it
            # if not self.is_magnetof_1_biased:
            #     data = data[data[:,-2] != MAGNETOF_1_CHANNEL ]
            # if not self.is_magnetof_2_biased:
            #     data = data[data[:,-2] != MAGNETOF_2_CHANNEL ]

            # THIS *SEEM* TO WORK FINE. The tof plot works fine. you have predefined tdc bins and it sorts each line 
            # according to its delta_t. Lines with 0 counts have delta_t == -1 which is not in the tdc bins
            # so it doesn't get sorted. So 0 counts get added nowhere
            # y,x = np.histogram(data[:,5]/2000, self.tdc_bins)
            y,x = np.histogram(data[:,5]/2000, np.linspace(self.tdc_start.value(),self.tdc_stop.value(),int((self.tdc_stop.value()-self.tdc_start.value())/self.tdc_bin.value())))
            self.hist = y
            # self.driver.setParam('Hist',self.hist)


            # TIME OF FLIGHT GATE
            gate1 = self.tofPlot.get_gate()
            if gate1:
                data = data[data[:,5]>gate1[0]*2000]
                data = data[data[:,5]<gate1[1]*2000]
            else:
                data = data

            #
            if len(data)>1:
                if time.time() - self.prev >= self.rate_interval.value():
                    self.prev = time.time()
                    if self.timeplot_rebin:
                        # FOR TIME-EVOLUTION PLOT
                        try:
                            y, _ = np.histogram(data[:,0], int( (data[-1,0] - data[0,0]) / self.rate_interval.value() ), weights=(data[:, -1]>-1).astype(int) )
                            self.rates = y
                            # self.driver.setParam('Counts',self.rates)
                        except:
                            pass
                        # self.timeplot_rebin = False
                    else:
                        # this line appends to self.rate the difference between the current number of datalines in self.data and the total number of lines ever received, which
                        # is basically the cumulative sum of all previous differences, which is the sum of self.rates. Not working well, needs remaking
                        # newdata = data
                        self.rates = np.append(self.rates, len(data) - np.sum(self.rates))
                        self.freqs.append(self.wavenumber)
                        # self.driver.setParam('Counts',self.rates[-1])
                        # self.driver.setParam('Counts_sum',self.driver.getParam('Counts_sum') + self.rates[-1])

                    # FOR SPECTRUM PLOT
                    # check if wavenumber bins have to be recalculated. if yes, it does it and updates the self.spectrum_bins, and raises the self.spectrum_rebin
                    self.check_max_min_wavenumber()
                    print(self.wavenumber)
                    # you need to rebin the spectrum, do it from scratch for all existing data
                    if self.spectrum_rebin:
                        try:
                            y, spectrum_bin_edges = np.histogram(data[:,1], self.spectrum_bins, weights=(data[:, -1]>-1).astype(int)/len(data) )
                            spectrum_bin_centers = spectrum_bin_edges[:-1] + np.diff(spectrum_bin_edges)/2
                            self.spectrum_y_vals = y
                            self.spectrum_x_vals = spectrum_bin_centers
                            # lower the flag
                            self.spectrum_rebin = False
                        except:
                            pass
                    else:
                        try:
                            # here it would be better to just use the known bins 
                            new_y, new_spectrum_bin_edges = np.histogram(new_data[:,1], self.spectrum_bins, weights=(data[:, -1]>-1).astype(int)/len(data) )
                            self.spectrum_y_vals += new_y
                            # new_spectrum_bin_edges = new_spectrum_bin_edges[:-1] + np.diff(new_spectrum_bin_edges)/2
                            # self.spectrum_x_vals = spectrum_bin_centers
                        except:
                            pass
        # try:
        #     print(self.rates[-1])
            # self.driver.setParam('Counts',self.rates[-1])
            # self.driver.setParam('Counts_sum',self.driver.getParam('Counts_sum') + self.rates[-1])
        # except Exception as e:
        #     print(e)
        # self.driver.updatePVs()
        # self.server.process(0.001)


    def check_max_min_wavenumber(self):
        update_bins = False
        if self.wavenumber < self.min_wvn_recorded:
            self.min_wvn_recorded = self.wavenumber
            update_bins = True
        if self.wavenumber > self.max_wvn_recorded:
            self.max_wvn_recorded = self.wavenumber
            update_bins = True

        # 
        if update_bins: # Time to recalculate the spectrum bins
            if self.min_wvn_recorded == self.initial_min_wvn_recorded or self.max_wvn_recorded == self.initial_max_wvn_recorded:
                self.spectrum_bins = np.linspace(self.min_wvn_recorded, self.max_wvn_recorded, int( abs(self.max_wvn_recorded - self.min_wvn_recorded) / 3 ))
                self.spectrum_rebin = True
            else: 
                self.spectrum_bins = np.linspace(self.min_wvn_recorded, self.max_wvn_recorded, int( abs(self.max_wvn_recorded - self.min_wvn_recorded)/self.bin_size_cm ))
                self.spectrum_rebin = True
            return
        else:
            return


    def update_spectrum_binsize(self):
        # convert binsize from MHz to /cm
        self.bin_size_cm = self.wavenumber_bin.value() * 0.0000334
        self.spectrum_bins = np.linspace(self.min_wvn_recorded, self.max_wvn_recorded, int( abs(self.max_wvn_recorded - self.min_wvn_recorded)/self.bin_size_cm ))
        self.spectrum_rebin = True
        return

    def update_tof_binsize(self):
        self.tdc_bins = np.linspace(self.tdc_start.value(),self.tdc_stop.value(),int((self.tdc_stop.value()-self.tdc_start.value())/self.tdc_bin.value()))


    def record_box_state_changed(self):
        if self.recordBox.isChecked():
            # if file is not None, it means theres sth open. close it and open new
            if self.record_file != None:
                self.record_file.close()
                self.record_file = None
            file_tsamp = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.now())
            self.file_name = SAVE_FILE_FOLDER + file_tsamp + '.csv'
            self.record_file = open(self.file_name, 'a')
            header = "['timestamp'],['wavenumber_1'],['bunch_no'],['events_per_bunch'],['channel'],['delta_t']\n"
            self.record_file.write(header)
        #
        # if the box is UNCHECKED
        else:
            if self.record_file != None:
                self.record_file.close()
                self.record_file = None


    # check if a magnetof is currently biased by comparing the current voltage supplied to it with some bias
    def check_if_magnetof_is_biased(self, magnetof, bias):
        channel = {1: 8, 2: 15}
        try:
            return caget('LaserLab:Module0:Channel{}:VoltageMeasure'.format(channel[magnetof])) > bias
        except Exception as e:
            print('magnetof bias test failed')
            print(e)
            return None

    def clear_data(self):
        del self.list_data
        del self.data
        del self.tdc_bins
        del self.hist
        del self.rates
        del self.freqs
        del self.spectrum_x_vals
        del self.spectrum_y_vals
        del self.time_plot_bins
        del self.rate
        if self.record_file != None:
            self.record_file.close()

        self.list_data = []
        self.data = None
         
        self.tdc_bins = np.linspace(self.tdc_start.value(),self.tdc_stop.value(),int((self.tdc_stop.value()-self.tdc_start.value())/self.tdc_bin.value()))
        self.hist = np.zeros(len(self.tdc_bins)-1)

        # self.driver.setParam('NoOfBins',len(self.hist))
        # self.driver.setParam('dt',self.tdc_bin.value())

        if self.file_name != None:
            self.record_file = open(self.file_name, 'a')
        self.rates = []
        self.freqs = []
        self.spectrum_x_vals = []
        self.spectrum_y_vals = []
        self.time_plot_bins = []
        self.rate = 0

    def closeEvent(self, event):
        self.running = False

        self.updateTimer.stop()
        self.wavenumberTimer.stop()
        self.calcTimer.stop()
        try:
            self.record_file.close()
        except:
            pass

        time.sleep(0.1)
        event.accept()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')

    window = Acquisition()
    sys.exit(app.exec_())
