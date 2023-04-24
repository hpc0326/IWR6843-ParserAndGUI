""" Module: utils """
import os
import json
import csv
import numpy as np
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
    
    def load_radar_data(self, filename):
        x = []
        y = []
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                npy_file = row[0]
                label = row[1]
                data = np.load(npy_file)
                x.append(data) # 只保留前三個欄位
                y.append(label)

        return x, y
