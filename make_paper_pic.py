import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

    def read_data(self, number):
        path = f"radar_data/{npy_file_name}_{number}.npy"
        np_array = np.load(path)
        dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'time']).drop('time', axis=1)

        # 只對不為 0 的值進行取相反數的操作
        nonzero_x_indices = dataframe['x'] != 0
        dataframe.loc[nonzero_x_indices, 'x'] = -dataframe.loc[nonzero_x_indices, 'x']
    
        return dataframe, path

    # def set_figure(self, title):
    #     # self.fig = plt.figure(figsize=(10, 10))
    #     self.fig = plt.figure()
    #     self.axes = self.fig.add_subplot(projection='3d')
    #     snr_nonzero_indices = np.nonzero(self.gesture_dataframe['snr'].values)[0]
    #     self.axes.scatter(self.gesture_dataframe['x'].values[snr_nonzero_indices],
    #                       self.gesture_dataframe['y'].values[snr_nonzero_indices],
    #                       self.gesture_dataframe['z'].values[snr_nonzero_indices],
    #                       c='b')  # 這裡設定了所有點的顏色為藍色
    #     self.axes.set_xlabel('X')
    #     self.axes.set_ylabel('Y')
    #     self.axes.set_zlabel('Z')
    #     self.axes.set_xlim([-0.6, 0.6])
    #     self.axes.set_ylim([0.6, 0])
    #     self.axes.set_zlim([-0.6, 0.6])
    #     self.axes.view_init(elev=10, azim=-90) ## 正面
    #     self.axes.view_init(elev=10, azim=180)  ## 側面
    #     self.axes.view_init(elev=80, azim=-90)  ## 俯視
    #     # plt.title(title)

    def set_figure(self, title):
        fig = plt.figure(figsize=(12, 12))  # 調整為 2x2 子圖的大小

        # 斜側面視角
        ax1 = fig.add_subplot(2, 2, 1, projection='3d')
        self.plot_data(ax1)
        ax1.view_init(elev=10, azim=-135)  
        ax1.set_title("Diagonal Side View")
        ax1.title.set_y(0.1)  # 調整標題的y坐標

        # 正面視角
        ax2 = fig.add_subplot(2, 2, 2, projection='3d')
        self.plot_data(ax2)
        ax2.view_init(elev=10, azim=-90)
        ax2.set_title("Front View")

        # 側面視角
        ax3 = fig.add_subplot(2, 2, 3, projection='3d')
        self.plot_data(ax3)
        ax3.view_init(elev=10, azim=180)
        ax3.set_title("Side View")

        # 俯視視角
        ax4 = fig.add_subplot(2, 2, 4, projection='3d')
        self.plot_data(ax4)
        ax4.view_init(elev=80, azim=-90)
        ax4.set_title("Top View")




    def plot_data(self, ax):
        snr_nonzero_indices = np.nonzero(self.gesture_dataframe['snr'].values)[0]
        ax.scatter(self.gesture_dataframe['x'].values[snr_nonzero_indices],
                   self.gesture_dataframe['y'].values[snr_nonzero_indices],
                   self.gesture_dataframe['z'].values[snr_nonzero_indices],
                   c='b')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_xlim([-0.6, 0.6])
        ax.set_ylim([0.6, 0])
        ax.set_zlim([-0.6, 0.6])
        # ax.set_xticklabels([])
        # ax.set_yticklabels([])
        # ax.set_zticklabels([])

    def run(self):
        self.file_number = input("請輸入要查看的檔案編號:")
        self.gesture_dataframe, self.file_path = self.read_data(self.file_number)
        print("1\n", self.gesture_dataframe)
        self.gesture_dataframe = self.gesture_dataframe.loc[self.gesture_dataframe['snr'] != 0].reset_index(drop=True)
        print(self.gesture_dataframe)

        self.set_figure(f'Filepath: {self.file_path}')
        output_file = 'radar_data_pic/pointcloud.png'
        plt.savefig(output_file, dpi=400, bbox_inches='tight', pad_inches=0.1)  # 調整 bbox_inches 和 pad_inches 參數
        # plt.savefig(output_file, dpi=800)  # 調整 dpi 參數以提高解析度
        print(f"圖片已儲存至 {output_file}")


if __name__ == '__main__':
    radar_viz = RadarDataVisualization()
    radar_viz.run()
