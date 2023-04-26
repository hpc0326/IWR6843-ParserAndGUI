"""This module contains the main application logic for processing and displaying radar data."""
from threading import Thread
from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI


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


def radar_thread_function():
    """radar_thread_function"""
    while True:
        data_ok, _, detection_obj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(data_ok, detection_obj)
        Radar.point_record(
                data_ok, avg_pt, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, DETECT_DIRECTION)
        if data_ok:
            GUI.store_point(avg_pt[:, :3])

radar_thread = Thread(target=radar_thread_function, args=())
radar_thread.daemon = True
radar_thread.start()

GUI.start(RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE)
