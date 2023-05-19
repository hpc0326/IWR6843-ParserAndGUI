from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
from modules.heatmap import HEATMAP
from modules.dot_gui import DOTDoppler
import time
import numpy as np
from threading import Thread

# 0: left / right detection; 1: up / down detection; 2: other detection
DETECT_DIRECTION = 0
#Point Cloud GUI
POINT_CLOUD_GUI = 0
#Heatmap GUI
HEATMAP_GUI = 1
#Dot version doppler
DOT_DOPPLER = 0


# Initialize classes
Utils = Utils()
Radar = Radar()
GUI = GUI()
HEATMAP = HEATMAP()
DOTDoppler = DOTDoppler()

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
        
        # if dataOk and POINT_CLOUD_GUI and not HEATMAP_GUI:
        #     GUI.store_point(avg_pt[:, :3])
            
        if dataOk and HEATMAP_GUI and not POINT_CLOUD_GUI:
            HEATMAP.save_data(detObj['doppler'], detObj['range'])
       
        if dataOk and DOT_DOPPLER:
            DOTDoppler.save_data(detObj['doppler'], detObj['range'])

if POINT_CLOUD_GUI:
    thread1 = Thread(target=process, args=(), daemon=True)
    thread1.start()
    GUI.start(RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE)


if HEATMAP_GUI:
    thread2 = Thread(target=process, args=(), daemon=True)
    thread2.start()
    HEATMAP.start()

if DOT_DOPPLER:
    thread3 = Thread(target=process, args=(), daemon=True)
    thread3.start()
    DOTDoppler.start()
# process()