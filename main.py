from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
import time

# Initialize calss
Utils = Utils()
Radar = Radar()

configFileName, cliPort, dataPort = Utils.get_config_json()

Radar.serialConfig(configFileName, cliPort, dataPort)

configParameters = Radar.parseConfigFile(configFileName)

while 1:
    dataOk, frameNumber, detObj = Radar.readAndParseData6843(configParameters)
    if dataOk:
        print(detObj)
