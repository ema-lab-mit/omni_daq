import epics
import numpy
import sys
import threading as th
from PyQt5 import QtWidgets, QtCore, uic

class DataServer(QtWidgets.QMainWindow):
    def __init__(self):
        super(DataServer, self).__init__()

        self.running = True

        self.wid = QtWidgets.QLabel('Data sever')
        self.setCentralWidget(self.wid)

        self.PVs = epics.PV('Scanner:PV', auto_monitor = True)
        self.PV_names = epics.PV('Scanner:PV_names', auto_monitor = True)
        self.to_save = epics.PV('Scanner:save_PV', callback = self.check_to_save, auto_monitor = True)

        self.loopThread = th.Thread(target = self.loop)
        self.loopThread.setDaemon(True)
        self.loopThread.start()

        self.show()

    def check_to_save(self, **kwargs):
        to_save = kwargs['value']
        PVs = self.PVs.get()

        self.PV = {}
        self.to_save = {}
        for i in range(len(PVs)):
            if not PVs[i] in self.PV.keys():
                self.PV[PVs[i]] = epics.PV(PVs[i], auto_monitor = True, callback = self.save_data)
            
            self.to_save[PVs[i]] = to_save[i]


    def save_data(self, **kwargs):
        if self.to_save[kwargs['pvname']]:
            with open(kwargs['pvname']):
                pass
                

    def loop(self):
        while self.running:
            epics.poll(0)

    def closeEvent(self, event):
        self.running = False
        event.accept()




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = DataServer()

    sys.exit(app.exec_())

    while True:
        epics.poll(0)