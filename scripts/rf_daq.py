import sys
from PyQt5 import QtGui, QtWidgets, QtCore, uic
import pyqtgraph as pg
import time
import numpy as np
import pandas as pd
import os
import threading as th
import epics
import sys
# Pathe to file
this_path = os.path.abspath(__file__)
father_path = os.path.abspath(os.path.join(this_path, "../../"))
print(father_path)
sys.path.append(father_path)

from modules.generator import RFGenerator

class RF(QtWidgets.QMainWindow):
    def __init__(self):
        super(RF, self).__init__()
        uic.loadUi(f'{father_path}/ui/files/rf_controller.ui.xml', self)

        self.scannr = 0
        for f in os.listdir(os.getcwd()):
            if 'data_on' in f:
                nr = int(f.strip('data_on').strip('.csv'))
                self.scannr = max(nr, self.scannr)

        print(self.scannr)

        self.setFreqButton.clicked.connect(self.setFreq)
        self.setPowerButton.clicked.connect(self.setPower)
        self.RFCheck.stateChanged.connect(self.toggleRF)
        self.startButton.clicked.connect(self.toggleScan)

        self.rf = RFGenerator()
        self.rf.toggle_buzzer(state = 'OFF')

        self.updateState(self.rf.get_state())
        self.updateFreq(self.rf.get_freq())

        self.prev = 0
        self.freq_on = []
        self.freq_off = []
        self.counts_on = []
        self.counts_off = []

        self.scanning = False
        self.loopTimer = QtCore.QTimer()
        self.loopTimer.timeout.connect(self.loop)
        self.loopTimer.setInterval(10)
        self.loopTimer.start()

        self.scanning = False
        self.plotTimer = QtCore.QTimer()
        self.plotTimer.timeout.connect(self.plot)
        self.plotTimer.setInterval(200)
        self.plotTimer.start()

        self.show()

    def updateFreq(self,freq):
        self.RFLabel.setText(str(round(freq,4)))

    def setFreq(self):
        freq = self.RFBox.value()
        self.rf.set_freq(freq)
        self.updateFreq(freq)

    def setPower(self):
        self.rf.set_power(self.powerBox.value())

    def toggleRF(self):
        self.rf.toggle_state(self.RFCheck.isChecked())

    def updateState(self, state):
        self.RFCheck.setChecked(state)

    def toggleUI(self, state):
        if state:
            self.startBox.setEnabled(True)
            self.stopBox.setEnabled(True)
            self.stepBox.setEnabled(True)
            self.setFreqButton.setEnabled(True)
            self.setPowerButton.setEnabled(True)
            self.RFCheck.setEnabled(True)
            self.powerBox.setEnabled(True)
            self.RFCheck.setEnabled(True)
            self.timeBox.setEnabled(True)
            self.RFBox.setEnabled(True)
            self.refCheck.setEnabled(True)
        else:
            self.startBox.setDisabled(True)
            self.stopBox.setDisabled(True)
            self.stepBox.setDisabled(True)
            self.setFreqButton.setDisabled(True)
            self.setPowerButton.setDisabled(True)
            self.RFCheck.setDisabled(True)
            self.powerBox.setDisabled(True)
            self.RFCheck.setDisabled(True)
            self.timeBox.setDisabled(True)
            self.RFBox.setDisabled(True)
            self.refCheck.setDisabled(True)

    def toggleScan(self):
        if self.scanning:
            self.scanning = False
            self.startButton.setText('Start')
            self.toggleUI(True)
        else:
            self.startButton.setText('Stop')
            self.toggleUI(False)

            self.scannr += 1

            self.counts_on = []
            self.counts_off = []
            self.freq_on = []
            self.freq_off = []

            self.start = self.startBox.value()
            self.stop = self.stopBox.value()
            self.step = self.stepBox.value()
            self.range = np.arange(self.start,self.stop,self.step)

            self.index = 0
            self.getCounts()
            self.rf.set_freq(self.range[self.index])
            self.updateFreq(self.range[self.index])
            self.rf.toggle_state(True)
            self.RFCheck.setChecked(True)
            self.last_time = time.time()

            self.dt = self.timeBox.value()
            self.ref = self.refCheck.isChecked()
            self.scanning = True

    def loop(self):
        if self.scanning:
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

    def getCounts(self):
        #counts = epics.caget('FURIOS:USBCTR8:1:Counter0:Counts')
        counts = epics.caget('RAPTOR:Counter:Counts_sum')
        ret = counts - self.prev
        self.prev = counts
        return ret

    def plot(self):
        if not self.scanning:
            return

        if self.ref:
            L = min(len(self.freq_on), len(self.freq_off))
            x,y = self.freq_on[:L], np.array(self.counts_on)[:L] - np.array(self.counts_off)[:L]
            self.plot1.plot(x,y,clear = True, pen='r')

            self.plot2.plot(self.freq_on, self.counts_on, clear = True, pen = 'r')
            self.plot2.plot(self.freq_off, self.counts_off, clear = False, pen = 'g')
        else:
            self.plot1.plot(self.freq_on, self.counts_on, clear = True, pen = 'r')

    def closeEvent(self, event):
        self.scanning = False
        self.plotTimer.stop()
        self.loopTimer.stop()
        event.accept() # let the window close

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pd.options.mode.chained_assignment = None
    window = RF()
    sys.exit(app.exec_())
