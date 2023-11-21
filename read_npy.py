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
        dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'azimuth', 'elevation'])
        return dataframe, path

    def set_figure(self, title, view):
        plt.close()
        self.fig = plt.figure()
        self.axes = self.fig.add_subplot(projection='3d')
        self.scatter = self.axes.scatter(self.gesture_dataframe['x'], self.gesture_dataframe['y'], self.gesture_dataframe['z'])
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')
        self.axes.set_zlabel('Z')
        self.axes.set_xlim([0.6, -0.6])
        self.axes.set_ylim([0.6, 0])
        self.axes.set_zlim([-0.6, 0.6])

        if view == 'b':
            self.axes.view_init(elev=80, azim=-90)  # 俯視（用於觀察左右、遠近的變化）
        elif view == 'c':
            self.axes.view_init(elev=5, azim=-150)  # 側面（用於觀察上下、遠近的變化）
        else :
            self.axes.view_init(elev=10, azim=-90)  # 正面（用於觀察上下、左右的變化）

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

    def run(self, file_number, view = 'a'):
        self.file_number = file_number
        if not os.path.exists(f"radar_data/{npy_file_name}_{self.file_number}.npy"):
            print(f"文件 {npy_file_name}_{self.file_number}.npy 不存在。")
            return False

        self.gesture_dataframe, self.file_path = self.read_data(self.file_number)
        print("All data\n", self.gesture_dataframe)
        # self.gesture_dataframe = self.gesture_dataframe.loc[self.gesture_dataframe['snr'] != 0].reset_index(drop=True)
        # print("No Zero\n", self.gesture_dataframe)

        self.set_figure(f'Filepath: {self.file_path}', view)
        animation = FuncAnimation(self.fig, self.update_plot, frames=len(self.gesture_dataframe), interval=20, blit=True)

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

    file_number = int(input("請輸入要查看的起始檔案編號: "))
    view = str(input("請輸入要查看的視角，a, b, c 分別為正面、俯視和側面視角: "))
    while True:
        status = radar_viz.run(file_number, view)
        if status == None:
            action = input("按 Enter 繼續到下一個文件，輸入新的編號來查看特定文件，或輸入 'd' 刪除當前文件: ")
            if action == 'd':
                try:
                    os.remove(f"radar_data/{npy_file_name}_{file_number}.npy")
                    print(f"文件 {npy_file_name}_{file_number}.npy 已被刪除。")
                    for suffix in ["azimuth", "doppler", "elevation", "range"]:
                        png_path = f"radar_data_pic/{npy_file_name}_{file_number}_{suffix}.png"
                        os.remove(png_path)
                        print(f"文件 {png_path} 已被刪除。")
                    file_number += 1
                except OSError as e:
                    print(f"文件刪除錯誤: {e}")
                    file_number += 1
            elif action.isdigit():
                print('digit')
                file_number = int(action)
            else:
                file_number += 1
        else:
            new_number = input("請輸入新的編號或按 Enter 換下一筆資料: ")
            if new_number.isdigit():
                file_number = int(new_number)
            else:
                file_number += 1
