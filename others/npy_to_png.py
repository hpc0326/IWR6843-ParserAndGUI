import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from dotenv import load_dotenv

load_dotenv()
npy_file_name = os.getenv("DATA_STORAGE_FILE_NAME")


def read_data(number):
    """
    从文件中读取数据并返回 DataFrame
    """
    path = f"radar_data/{npy_file_name}_{number}.npy"
    np_array = np.load(path)
    dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'time'])
    return dataframe, path


def plot_data_3d(dataframe, title):
    """
    將數據以3D散點圖形式進行可視化並保存為PNG文件。
    """
    fig = plt.figure()
    axes = fig.add_subplot(projection='3d')
    axes.scatter(dataframe['x'], dataframe['y'], dataframe['z'])
    axes.set_xlabel('X')
    axes.set_ylabel('Y')
    axes.set_zlabel('Z')
    axes.set_title(title)
    # 調整座標範圍
    axes.set_xlim([0.6, -0.6])
    axes.set_ylim([0.6, 0])
    axes.set_zlim([-0.6, 0.6])
    # 調整視角
    # axes.view_init(elev=90, azim=-90)   # 俯視(x, y 平面)（用於觀察左右、遠近的變化）
    axes.view_init(elev=0, azim=-90)   # 正面(x, z 平面)（用於觀察上下、左右的變化）
    # axes.view_init(elev=0, azim=-180)   # 側面(y, z 平面)（用於觀察上下、遠近的變化）
    plt.savefig(f"radar_data_png/{title}.png")
    plt.close()

if __name__ == '__main__':
    file_number = input("請輸入要查看的檔案編號:")
    gesture_dataframe, file_path = read_data(file_number)
    print(gesture_dataframe)
    plot_data_3d(gesture_dataframe, f"Gesture {file_number}")
