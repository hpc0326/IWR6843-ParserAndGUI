from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
import time

# Initialize calss
Utils = Utils()
Radar = Radar()
GUI = GUI()

RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH = Utils.get_radar_env()
cli_serial, data_serial = Radar.start(RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH)
while 1:
    detObj = Radar.read_and_parse_radar_data(data_serial)
    print(detObj)
    time.sleep(0.1)
# RADAR_POSISION_X, RADAR_POSISION_Y, RADAR_POSISION_Z, GRID_SIZE= Utils.get_gui_env()
# GUI.start(RADAR_POSISION_X, RADAR_POSISION_Y, RADAR_POSISION_Z, GRID_SIZE)
