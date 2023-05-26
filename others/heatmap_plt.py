import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()
npy_file_name = os.getenv("DATA_STORAGE_FILE_NAME")

def read_data(number):
    """
    從檔案中讀取資料並以 DataFrame 的形式返回
    """
    path = f"radar_data/{npy_file_name}_{number}.npy"
    np_array = np.load(path)
    dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'time'])
    return dataframe, path

if __name__ == '__main__':
    file_number = input("請輸入要查看的檔案編號:")
    gesture_dataframe, file_path = read_data(file_number)
    print(gesture_dataframe['doppler'])
   
    # generate 2 2d grids for the x & y bounds
    y, x = np.meshgrid(np.linspace(-2.5, 2.5, 32), np.linspace(0, 10, 32))

    z = np.zeros((32,32))
    #plot the data in the grid
    for i, j in enumerate(gesture_dataframe['range']):
        z[int(j*32)][int((gesture_dataframe['doppler'][i]+2.5)*32/5)] = 1

    z = z[:-1, :-1]
    z_min, z_max = -np.abs(z).max(), np.abs(z).max()

    fig, ax = plt.subplots()

    c = ax.pcolormesh(x, y, z, cmap='RdBu', vmin=z_min, vmax=z_max)
    ax.set_title('range-doppler')
    ax.axis([x.min(), x.max(), y.min(), y.max()])
    

    plt.savefig('figure.png')