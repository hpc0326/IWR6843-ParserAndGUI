''' Module: gui '''
import sys
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np

class DOTDoppler():
    ''' Class GUI '''

    def __init__(self):
        
        self.point_data = np.array([[0.0 ,0.0 ,0.0]])
        self.point_cloud = None
        self.data = None
        
        print('''[Info] Initialize GUI class ''')

    def start(self):
        """ start """
        # pylint: disable=W0612
        
        app = QtWidgets.QApplication([])
        gl_view = pg.GraphicsView()
        l = pg.GraphicsLayout()
        # gl_view.setBackgroundColor(QtGui.QColor(0, 0, 0))
        gl_view.show()
        gl_view.setCentralItem(l)
        gl_view.resize(800,600) 
        p0 = l.addPlot(1, 1)
        p0.showGrid(x = True, y = True, alpha = 5)
        # l.layout.setSpacing(0.)
        # l.setContentsMargins(0.8, 0.8, 0.8, 0.8)

        # self.initialize_point_cloud(gl_view)
        timer = QtCore.QTimer()
        self.setTimer(timer)
        # app.exec_()
        if sys.flags.interactive != 1:
            if not hasattr(QtCore, 'PYQT_VERSION'):
                QtGui.QApplication.instance().exec()


    def grid_settings(self, gl_view, grid_size):
        """ grid_settings """
        # cube = gl.GLBoxItem(size=QtGui.QVector3D(
        #     grid_size, grid_size, grid_size))
        # cube.translate(-(grid_size/2), 0, -(grid_size/2))
        # gl_view.addItem(cube)

        gxy = gl.GLGridItem()  # Three-dimensional grid
        gxy.setSize(x=grid_size, y=grid_size, z=grid_size)
        gxy.setSpacing(x=0.1, y=0.1, z=0.1)
        gxy.translate(0, grid_size/2, -(grid_size/2))
        gxy.setColor((255, 255, 255, 60))
        gl_view.addItem(gxy)

    def initialize_point_cloud(self, gl_view):
        """ initialize_point_cloud """
        self.point_cloud = gl.GLScatterPlotItem(pos=np.zeros((80, 2)), color=[
                                           0, 255, 240, 255], size=10.0)
        gl_view.addItem(self.point_cloud)
        
    def update_point(self):
        self.point_cloud.setData(pos=self.point_data)

    def setTimer(self, t):
        t.timeout.connect(self.update_point)
        t.start(50)

    def save_data(self, doppler, range):
        self.data = np.zeros((32, 50))
        for i, j in enumerate(range) :
            self.data[int(range[i]+2)*8][int(doppler[i]+2)*8] = 1500
    