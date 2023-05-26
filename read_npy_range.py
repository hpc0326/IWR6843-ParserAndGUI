"""讀取 .npy 檔案，並透過(x, y, z)座標計算 range"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()
npy_file_name = os.getenv("DATA_STORAGE_FILE_NAME")


def read_data(number):
    """
    讀取 .npy 檔案資料並轉換為 dataframe
    """
    path = f"radar_data/{npy_file_name}_{number}.npy"
    np_array = np.load(path)
    dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'time'])
    return dataframe, path

def get_range(dataframe):
    dataframe['range_calc'] = np.sqrt(dataframe['x']**2 + dataframe['y']**2 + dataframe['z']**2)

    
if __name__ == '__main__':
    file_number = input("請輸入檔案編號：")
    gesture_dataframe, file_path = read_data(file_number)
    get_range(gesture_dataframe)
    
    # 調整欄位順序
    new_column_order = ['x', 'y', 'z', 'doppler', 'range', 'range_calc', 'snr', 'time']
    gesture_dataframe = gesture_dataframe[new_column_order]
    
    print(gesture_dataframe)
