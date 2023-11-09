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


class RadarDataVisualization:
    def __init__(self):
        self.file_number = None
        self.gesture_dataframe = None
        self.file_path = None
        self.fig = None
        self.axes = None
        self.scatter = None

    def read_data(self, number):
        path = f"radar_data/{npy_file_name}_{number}.npy"
        np_array = np.load(path)
        dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'azimuth', 'elevation', 'time']).drop('time', axis=1)
        return dataframe, path

    def set_figure(self, title):
        self.fig = plt.figure()
        self.axes = self.fig.add_subplot(projection='3d')
        self.scatter = self.axes.scatter(self.gesture_dataframe['x'], self.gesture_dataframe['y'], self.gesture_dataframe['z'])
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')
        self.axes.set_zlabel('Z')
        self.axes.set_xlim([0.6, -0.6])
        self.axes.set_ylim([0.6, 0])
        self.axes.set_zlim([-0.6, 0.6])
        self.axes.view_init(elev=-90, azim=90)
        plt.title(title)

    def update_plot(self, frame):
        snr_nonzero_indices = np.nonzero(self.gesture_dataframe['snr'][:frame+1].values)[0]
        self.scatter._offsets3d = (
            self.gesture_dataframe['x'][:frame+1].values[snr_nonzero_indices],
            self.gesture_dataframe['y'][:frame+1].values[snr_nonzero_indices],
            self.gesture_dataframe['z'][:frame+1].values[snr_nonzero_indices]
        )
        self.scatter.set_array(range(len(snr_nonzero_indices)))
        self.scatter.set_cmap('plasma')
        self.scatter.set_clim(0, len(snr_nonzero_indices))
        return self.scatter,

    def run(self):
        self.file_number = input("請輸入要查看的檔案編號:")
        self.gesture_dataframe, self.file_path = self.read_data(self.file_number)
        print("All data\n", self.gesture_dataframe)
        self.gesture_dataframe = self.gesture_dataframe.loc[self.gesture_dataframe['snr'] != 0].reset_index(drop=True)
        print("No Zero\n", self.gesture_dataframe)

        self.set_figure(f'Filepath: {self.file_path}')
        animation = FuncAnimation(self.fig, self.update_plot, frames=len(self.gesture_dataframe), interval=40, blit=True)

        output_file = 'radar_data_gif/PointCloud_animation.gif'
        animation.save(output_file, writer='pillow')
        print(f"圖片已儲存至 {output_file}")

    def get_animation(self, dataframe):
        self.gesture_dataframe = dataframe
        self.gesture_dataframe = self.gesture_dataframe.loc[self.gesture_dataframe['snr'] != 0].reset_index(drop=True)
        print(self.gesture_dataframe)

        self.set_figure(f'Filepath: {self.file_path}')
        animation = FuncAnimation(self.fig, self.update_plot, frames=len(self.gesture_dataframe), interval=40, blit=True)

        output_file = 'radar_data_gif/PointCloud_animation.gif'
        animation.save(output_file, writer='pillow')
        print(f"圖片已儲存至 {output_file}")


if __name__ == '__main__':
    radar_viz = RadarDataVisualization()
    radar_viz.run()
