""" Module: utils """
import os
import json
# from dotenv import load_dotenv

class Utils:
    """ Class: Utils """
    def __init__(self):
        print('''[Info] Initialize Utils class ''')

    def get_config_json(self): # 新的
        """ Reading configuration.json"""
        with open('configuration.json') as configfile:
            data = json.load(configfile)
            configFileName = data['configFileName']
            cliPort = data['cliPort']
            dataPort = data['dataPort']

            return configFileName, cliPort, dataPort
