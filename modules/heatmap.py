''' Module: gui '''
import sys
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
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
        self.data = np.random.normal(size=(256, 32))
        print(self.data)
        self.rangeAry = None
        self.dopplerAry = None
        self.rangeDpr = None

        print('''[Info] Initialize HEATMAP class ''')

    def start(self):
        """ start """
        app = QtWidgets.QApplication(sys.argv)
        window = pg.GraphicsLayoutWidget()
        image = pg.ImageItem()
        print(self.data)
        print(type(self.data))
        self.data[40:80, 40:120] += 4
        self.data = pg.gaussianFilter(self.data, (15, 15))
        image.setLookupTable(self.look_up_table)  # Add
        image.setImage(self.data)
        view_box = pg.ViewBox()
        view_box.addItem(image)
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
       

    def setTimer(self, t):
        t.timeout.connect(self.update)
        t.start(100)
    
    def save_data(self, rangeDpr, rangeAry, dopplerAry):
        print('save data')
        self.rangeDpr = rangeDpr
        self.rangeAry = rangeAry
        self.dopplerAry = dopplerAry