""" Module: utils """
import os
import csv
import numpy as np
from dotenv import load_dotenv

class Utils:
    """ Class: Utils """
    def __init__(self):
        print('''[Info] Initialize Utils class ''')

    def get_radar_env(self):
        """ Reading environmental variables """
        # Load .env file
        load_dotenv()
        # Access environment variables
        radar_cli_port = os.environ.get("RADAR_CLI_PORT")
        radar_data_port = os.environ.get("RADAR_DATA_PORT")
        radar_config_prefix_path = os.environ.get("RADAR_CONFIG_PREFIX_PATH")
        radar_config_file_name = os.environ.get("RADAR_CONFIG_FILE_NAME")
        data_storage_file_path = os.environ.get("DATA_STORAGE_FILE_PATH")
        data_storage_file_name = os.environ.get("DATA_STORAGE_FILE_NAME")
        pic_storage_file_name = os.environ.get("IMAGE_STORAGE_FILE_PATH")
        radar_config_file_path = f'''{radar_config_prefix_path}/{radar_config_file_name}'''
        print(
            f'''[Info] RADAR_CLI_PORT: {radar_cli_port}\n''' +
            f'''[Info] RADAR_DATA_PORT: {radar_data_port}\n''' +
            f'''[Info] RADAR_CONFIG_FILE_PATH: {radar_config_file_path}'''
        )
        return radar_cli_port, radar_data_port, radar_config_file_path, data_storage_file_path, data_storage_file_name, pic_storage_file_name

    def get_gui_env(self):
        """ Reading environmental variables """
        # Load .env file
        load_dotenv()
        # Access environment variables
        radar_position_x = float(os.environ.get("RADAR_POSISION_X"))
        radar_position_y = float(os.environ.get("RADAR_POSISION_Y"))
        radar_position_z = float(os.environ.get("RADAR_POSISION_Z"))
        grid_size = int(os.environ.get("GRID_SIZE"))
        print(
            f'''[Info] RADAR_POSISION_X: {radar_position_x}\n''' +
            f'''[Info] RADAR_POSISION_Y: {radar_position_y}\n''' +
            f'''[Info] RADAR_POSISION_X: {radar_position_z}\n''' +
            f'''[Info] GRID_SIZE: {grid_size}'''
        )
        return radar_position_x, radar_position_y, radar_position_z, grid_size
    
    def load_radar_data(self, filename):
        """ load_radar_data """
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
