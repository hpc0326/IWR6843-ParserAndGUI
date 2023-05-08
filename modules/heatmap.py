''' Module: gui '''
import sys
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np
from colour import Color

class HEATMAP():
    ''' Class GUI '''

    def __init__(self):
        self.blue = Color('blue')
        self.red = Color('red')
        self.colors = self.blue.range_to(self.red, 256)
        self.colors_array = np.array([np.array(color.get_rgb()) * 255 for color in self.colors])
        self.look_up_table = self.colors_array.astype(np.uint8)
        self.data = np.zeros((32, 256))
        self.rangeAry = None
        self.dopplerAry = None
        self.rangeDpr = None
        self.image = None
        print('''[Info] Initialize HEATMAP class ''')

    def start(self):
        """ start """
        app = QtWidgets.QApplication([])
        window = pg.GraphicsLayoutWidget()
        self.image = pg.ImageItem()
        self.image.setLookupTable(self.look_up_table)  # Add
        self.image.setImage(self.data)
        view_box = pg.ViewBox()
        view_box.addItem(self.image)
        plot = pg.PlotItem(viewBox=view_box)
        window.addItem(plot)
        
        timer = QtCore.QTimer()
        self.setTimer(timer)
        window.show()
        
        if sys.flags.interactive != 1:
            if not hasattr(QtCore, 'PYQT_VERSION'):
                QtWidgets.QApplication.instance().exec()


    def update(self):
        self.data = self.dopplerAry
        self.image.setImage(self.data)
        #print doppler array
        print(self.data)

    def setTimer(self, t):
        t.timeout.connect(self.update)
        t.start(100)
    
    def save_data(self, rangeDpr, rangeAry, dopplerAry):
        self.rangeDpr = rangeDpr #useless
        self.rangeAry = rangeAry #useless
        self.dopplerAry = np.transpose(dopplerAry) 