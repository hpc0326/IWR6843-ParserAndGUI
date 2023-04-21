from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
import time

directory = "./radar_data"
direction = 0 # 0: left / right detection; 1: up / down detection; 2: other detection

# Initialize calss
Utils = Utils()
Radar = Radar()

configFileName, cliPort, dataPort = Utils.get_config_json()

Radar.serialConfig(configFileName, cliPort, dataPort)

configParameters = Radar.parseConfigFile(configFileName)

while 1:
    dataOk, frameNumber, detObj = Radar.readAndParseData6843(configParameters)
    avg_pt = Radar.find_average_point(dataOk, detObj)
    Radar.point_record(dataOk, avg_pt, directory, direction)
