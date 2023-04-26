from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
from pyqtgraph.Qt import QtCore
import time
import numpy as np
import queue
import threading

# 0: left / right detection; 1: up / down detection; 2: other detection
DETECT_DIRECTION = 0

# Initialize classes
Utils = Utils()
Radar = Radar()
GUI = GUI()

RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME = Utils.get_radar_env()
cli_serial, data_serial = Radar.start(
    RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH)

RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE = Utils.get_gui_env()


def radar_thread_function(avg_pt_queue):
    """radar_thread_function"""
    while True:
        data_ok, _, detection_obj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(data_ok, detection_obj)
        if data_ok:
            avg_pt_queue.put(avg_pt)
        Radar.point_record(
            data_ok, avg_pt, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, DETECT_DIRECTION)
        # print('avg_pt_queue', avg_pt_queue.get())

# 在主線程中創建一個Queue對象
avg_pt_queue = queue.Queue()

# 在子線程中執行雷達數據處理
radar_thread = threading.Thread(target=radar_thread_function, args=(avg_pt_queue,))
radar_thread.start()

# 在主線程中執行GUI.start函數
GUI.start(RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE, avg_pt_queue)



# while True:
#     # print('------ in while ------')
#     dataOk, frameNumber, detObj = Radar.read_and_parse_radar_data(data_serial)
#     avg_pt = Radar.find_average_point(dataOk, detObj)
#     Radar.point_record(
#         dataOk, avg_pt, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, DETECT_DIRECTION)
