import pyqtgraph as pg
from PyQt5 import QtGui,QtCore,QtWidgets
import numpy as np

class BinPlotWidget(QtWidgets.QWidget):
    new_gate = QtCore.Signal()
    def __init__(self,*args,**kwargs):
        super(BinPlotWidget,self).__init__()
        

        self.plotwidget = GatePlotWidget(*args,**kwargs)
        self.plotwidget.new_gate.connect(self.new_gate.emit)

        self.curve = pg.PlotCurveItem()
        self.plotwidget.addItem(self.curve)
        
        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(self.plotwidget,0,0,1,3)

    def get_gate(self):
        return self.plotwidget.get_gate()
                
class GatePlotWidget(pg.PlotWidget):
    new_gate = QtCore.Signal()
    def __init__(self,*args,**kwargs):
        kwargs['viewBox'] = GateViewBox()
        super(GatePlotWidget,self).__init__(*args,**kwargs)
        self.plotItem.vb.new_gate.connect(self.emit_new_gate)

    def emit_new_gate(self):
        self.new_gate.emit()

    def get_gate(self):
        region = self.plotItem.vb.region
        if not region:
            return region
        else:
            return region.getRegion()

class GateViewBox(pg.ViewBox):
    new_gate = QtCore.Signal()
    def __init__(self,*args,**kwargs):
        super(GateViewBox,self).__init__(*args,**kwargs)
        self.region = None
        self.gate = None

    def mouseDragEvent(self,ev,axis=None):
        if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            start = self.mapSceneToView(ev.buttonDownScenePos())
            finish = self.mapSceneToView(ev.scenePos())

            gate = [start.x(),finish.x()]
            if not self.region:
                self.region = GateRegion(values = gate,
                        movable=True)
                self.region.remove_me.connect(self.removeRegion)
                self.region.sigRegionChanged.connect(self.new_gate.emit)
                self.addItem(self.region)
            else:
                self.region.setRegion(gate)

            if ev.isFinish():
                self.new_gate.emit()
        else:
            super(GateViewBox,self).mouseDragEvent(ev)

        ev.accept()

    def removeRegion(self):
        self.new_gate.emit()
        self.removeItem(self.region)
        self.region = None

class GateRegion(pg.LinearRegionItem):
    remove_me = QtCore.Signal()
    def __init__(self,*args,**kwargs):
        super(GateRegion,self).__init__(*args,**kwargs)
    
    def mouseDoubleClickEvent(self,ev):
        self.remove_me.emit()
        
        
        
