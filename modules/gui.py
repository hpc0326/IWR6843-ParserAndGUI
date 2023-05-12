''' Module: gui '''
import sys
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np
from colour import Color


class GUI():
    ''' Class GUI '''

    def __init__(self):
        self.point_cloud = None
        self.point_data = np.array([[0.0 ,0.0 ,0.0]])
        print('''[Info] Initialize GUI class ''')

        self.colors = list(Color("purple").range_to(Color("red"), 256))
        self.colors_array = np.array([np.array(color.get_rgb()) * 255 for color in self.colors])
        self.look_up_table = self.colors_array.astype(np.uint8)
        self.range_doppler_data = np.zeros((32, 256))
        self.range_array = None
        self.doppler_array = None
        self.range_doppler = None
        self.heatmap = None
        print('''[Info] Initialize HEATMAP class ''')


    def start(self, radar_position_x, radar_position_y, radar_position_z, grid_size):
        """ start """
        # pylint: disable=W0612
        app = QtWidgets.QApplication([])
        gl_view = gl.GLViewWidget()
        gl_view.setBackgroundColor(QtGui.QColor(0, 0, 0))
        gl_view.show()
        self.radar_position_settings(
            gl_view, radar_position_x, radar_position_y, radar_position_z)
        self.grid_settings(gl_view, grid_size)
        self.coordinate_axis_settings(gl_view)
        self.view_angle_settings(gl_view)
        self.initialize_point_cloud(gl_view)
        timer = QtCore.QTimer()
        self.set_timer(timer)

        window = pg.GraphicsLayoutWidget()
        self.heatmap = pg.ImageItem()
        self.heatmap.setLookupTable(self.look_up_table)  # Add
        self.heatmap.setImage(self.range_doppler_data)
        view_box = pg.ViewBox()
        view_box.addItem(self.heatmap)
        plot = pg.PlotItem(viewBox=view_box)
        window.addItem(plot)
        
        # timer = QtCore.QTimer()
        # self.setTimer(timer)
        window.show()

        if sys.flags.interactive != 1:
            if not hasattr(QtCore, 'PYQT_VERSION'):
                QtWidgets.QApplication.instance().exec()

    def radar_position_settings(self, gl_view, radar_position_x, radar_position_y, radar_position_z):
        """ radar_position_settings """
        print('''[Info] Radar device starting''')
        vertexes_np = np.empty((2, 3, 3))  # Vertex coordinates
        vertexes_np[0, 0, :] = [-radar_position_x,
                                radar_position_y,  radar_position_z]
        vertexes_np[0, 1, :] = [-radar_position_x,
                                radar_position_y, -radar_position_z]
        vertexes_np[0, 2, :] = [radar_position_x,
                                radar_position_y, -radar_position_z]
        vertexes_np[1, 0, :] = [-radar_position_x,
                                radar_position_y,  radar_position_z]
        vertexes_np[1, 1, :] = [radar_position_x,
                                radar_position_y,  radar_position_z]
        vertexes_np[1, 2, :] = [radar_position_x,
                                radar_position_y, -radar_position_z]
        radar_position = gl.GLMeshItem(vertexes=vertexes_np, smooth=False,
                                       drawEdges=True, edgeColor=pg.glColor('r'), drawFaces=False)
        gl_view.addItem(radar_position)

    def grid_settings(self, gl_view, grid_size):
        """ grid_settings """
        cube = gl.GLBoxItem(size=QtGui.QVector3D(
            grid_size, grid_size, grid_size))
        cube.translate(-(grid_size/2), 0, -(grid_size/2))
        gl_view.addItem(cube)

        gxy = gl.GLGridItem()  # Three-dimensional grid
        gxy.setSize(x=grid_size, y=grid_size, z=grid_size)
        gxy.setSpacing(x=0.1, y=0.1, z=0.1)
        gxy.translate(0, grid_size/2, -(grid_size/2))
        gxy.setColor((255, 255, 255, 60))
        gl_view.addItem(gxy)

        gyz = gl.GLGridItem()  # Three-dimensional grid
        gyz.setSize(x=grid_size, y=grid_size, z=grid_size)
        gyz.rotate(90, 0, 1, 0)
        gyz.setSpacing(x=0.1, y=0.1, z=0.1)
        gyz.translate(-(grid_size/2), grid_size/2, 0)
        gyz.setColor((255, 255, 255, 60))
        gl_view.addItem(gyz)

        gzx = gl.GLGridItem()  # Three-dimensional grid
        gzx.setSize(x=grid_size, y=grid_size, z=grid_size)
        gzx.rotate(90, 1, 0, 0)
        gzx.setSpacing(x=0.1, y=0.1, z=0.1)
        gzx.translate(0, 0, 0)
        gzx.setColor((255, 255, 255, 60))
        gl_view.addItem(gzx)

    def coordinate_axis_settings(self, gl_view):
        """ coordinate_axis_settings """
        axis = gl.GLAxisItem(glOptions='opaque')
        axis.setSize(0.5, 0.5, 0.5)
        axis.translate(0, 0, 0)
        axis.rotate(90, 0, 0, 1)
        gl_view.addItem(axis)

    def view_angle_settings(self, gl_view):
        """ view_angle_settings """
        gl_view.setCameraPosition(distance=5, elevation=0, azimuth=90)

    def initialize_point_cloud(self, gl_view):
        """ initialize_point_cloud """
        self.point_cloud = gl.GLScatterPlotItem(pos=np.zeros((100, 3)), color=[
                                           0, 255, 240, 255], size=10.0)
        gl_view.addItem(self.point_cloud)

    def update_point(self):
        """ update_point """
        self.point_cloud.setData(pos=self.point_data)
        self.range_doppler_data = self.range_doppler
        self.heatmap.setImage(self.range_doppler_data)

    def set_timer(self, timer):
        """ set_timer """
        timer.timeout.connect(self.update_point)
        timer.start(50)

    def store_point(self, point):
        """ store_point """
        self.point_data = point
        print(point)

    def save_data(self, range_array, doppler_array, range_doppler):
        self.range_array = range_array #useless
        self.doppler_array = doppler_array #useless
        self.range_doppler = np.transpose(range_doppler) 
        