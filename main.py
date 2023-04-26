from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
import time
import numpy as np
from threading import Thread

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


def process():
    while 1:
        dataOk, frameNumber, detObj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(dataOk, detObj)
        Radar.point_record(
                dataOk, avg_pt, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, DETECT_DIRECTION)
        if dataOk:
            GUI.store_point(avg_pt[:, :3])
       


thread1 = Thread(target=process, args=())
thread1.setDaemon(True)
thread1.start()

GUI.start(RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE)
