"""This module contains the main application logic for processing and displaying radar data."""
from threading import Thread
from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
# from modules.heatmap import HEATMAP
import time
import numpy as np
from threading import Thread

# 0: left / right detection; 1: up / down detection; 2: other detection
DETECT_DIRECTION = 0
#Point Cloud GUI
POINT_CLOUD_GUI = 1
#Heatmap GUI
HEATMAP_GUI = 0


# Initialize classes
Utils = Utils()
Radar = Radar()
GUI = GUI()

RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME = Utils.get_radar_env()
cli_serial, data_serial, radar_parameters = Radar.start(
    RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH)

RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE = Utils.get_gui_env()

def radar_thread_function():
    """radar_thread_function"""
    while True:
        data_ok, _, detection_obj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(data_ok, detection_obj)
        doppler_array = Radar.heatmap_handler(data_ok, detection_obj)
        Radar.point_record(
                data_ok, avg_pt, doppler_array, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, DETECT_DIRECTION)

        # if data_ok:
        #     # print('detection_obj:\n', detection_obj)
        #     GUI.store_point(avg_pt[:, :3])
        if data_ok and POINT_CLOUD_GUI and not HEATMAP_GUI:
            GUI.store_point(avg_pt[:, :3])
            GUI.save_data(radar_parameters['doppler_parameters']['range_array'], radar_parameters['doppler_parameters']['doppler_array'], detection_obj['rangeDoppler'])

# radar_thread = Thread(target=radar_thread_function, args=())
# radar_thread.daemon = True
# radar_thread.start()

# GUI.start(RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE)

if POINT_CLOUD_GUI:
    radar_thread = Thread(target=radar_thread_function, args=())
    radar_thread.daemon = True
    radar_thread.start()
    GUI.start(RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE)