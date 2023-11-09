import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dotenv import load_dotenv
import csv 


load_dotenv()
npy_file_name = os.getenv("DATA_STORAGE_FILE_NAME")
npy_file_dir = os.getenv("DATA_STORAGE_FILE_PATH")


def read_data(number):
    """
    從檔案中讀取資料並以 DataFrame 的形式返回
    """
    path = f"radar_data/{npy_file_name}_{number}.npy"
    np_array = np.load(path)
    dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'time'])
    return dataframe, path

def write_label(filename, label):
    with open('radar_data_csv/np_label.csv', 'a+', newline='', encoding='utf-8') as csvfile:
        demo_writer = csv.writer(
            csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
        demo_writer.writerow([filename, label])

def labeling_deviation():
    pass

def labeling_basic(df, filename, direction):

    if direction == 0:
        wave_end_pt = df['x'].values[0]
        wave_start_pt = df['x'].values[-1]

        if wave_end_pt > wave_start_pt:
            print("left wave")
            write_label(filename, 'right wave')
            
 

        elif wave_end_pt < wave_start_pt:
            print("right wave")
            write_label(filename, 'left wave')
            

    if direction == 1:
        wave_end_pt = df['z'].values[0]
        wave_start_pt = df['z'].values[-1]
        if wave_end_pt > wave_start_pt:
            print("up wave")
            write_label(filename, 'up wave')
  

        elif wave_end_pt < wave_start_pt:
            print("down wave")
            write_label(filename, 'down wave')
            
        

if __name__ == '__main__':
    
    file_number = input("請輸入要查看的檔案編號:")
    df, path = read_data(file_number)
    #delete zero data
    df = df.loc[df['x']!=0]
    direction = 0
    
    labeling_basic(df, f'./{path}', direction)
