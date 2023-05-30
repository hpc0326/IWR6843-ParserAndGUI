"""
讀取包含每個動作的雷達資料的 .npy 檔案，並將這些資料可視化存成 .gif 檔案。
程式執行後會顯示 "請輸入要查看的檔案編號:"
假如檔案名稱為 yuan_data_55.npy 則輸入 55
輸入後會在 Terminal 上印出這個手勢中每一個點的 (x, y, z) 座標以及出現的時間
並且將這些點做成動畫存成 PointCloud_animation.gif 檔案，其中點的顏色由深至淺表示先後順序
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
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


def set_figure(dataframe, title):
    
    fig = plt.figure()
    axes = fig.add_subplot(projection='3d')
    scatter = axes.scatter(dataframe['x'], dataframe['y'], dataframe['z'])
    axes.set_xlabel('X')
    axes.set_ylabel('Y')
    axes.set_zlabel('Z')
    # 調整座標範圍
    axes.set_xlim([0.6, -0.6])
    axes.set_ylim([0.6, 0])
    axes.set_zlim([-0.6, 0.6])
    # 調整視角
    axes.view_init(elev=80, azim=-90)   # 俯視（用於觀察左右、遠近的變化）
    # axes.view_init(elev=10, azim=-90)   # 正面（用於觀察上下、左右的變化）
    # axes.view_init(elev=5, azim=-150)   # 側面（用於觀察上下、遠近的變化）
    plt.title(title)
    return fig, axes, scatter


def animate(path, dataframe, interval):
    """
    生成動畫
    """
    fig, _, scatter = set_figure(dataframe, f'Filepath: {path}')
    plot = FuncAnimation(fig, update_scatter, frames=range(0, int(
        dataframe['time'].max() * 30)), interval=interval, blit=True, fargs=(dataframe, scatter))
    return plot


def update_scatter(frame, dataframe, scatter):
    """
    更新 Point Cloud 的座標和顏色等資料
    """
    current_time = frame / 30.0
    current_data = dataframe[dataframe['time'] <= current_time]
    color_min = dataframe['time'].min()
    color_max = dataframe['time'].max()
    colors = current_data['time'].values
    scatter._offsets3d = (
        current_data['x'], current_data['y'], current_data['z'])
    scatter.set_array(colors)
    scatter.set_cmap('plasma')
    scatter.set_clim(color_min, color_max)
    return scatter,


if __name__ == '__main__':
    file_number = input("請輸入要查看的檔案編號:")
    gesture_dataframe, file_path = read_data(file_number)
    print(gesture_dataframe)
    animation = animate(file_path, gesture_dataframe, interval=33)
    animation.save('radar_data_gif/PointCloud_animation.gif')
    # plt.show()  # 打開 3D 圖的視窗
