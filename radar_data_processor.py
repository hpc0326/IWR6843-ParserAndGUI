"""讀取 .npy 將資料可視化，再透過二值化、resize等操作獲得手勢點雲的圖片"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import cv2

class RadarDataProcessor:
    def __init__(self):
        load_dotenv()
        self.npy_file_name = os.getenv("DATA_STORAGE_FILE_NAME")

    def read_data(self, number):
        """
        讀取 .npy 檔案資料並轉換為 dataframe
        """
        # path = f"radar_data/{self.npy_file_name}_{number}.npy"
        path = f"radar_data_feng/feng_data_{number}.npy"
        np_array = np.load(path)
        dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'doppler', 'range', 'snr', 'time'])
        # dataframe = pd.DataFrame(np_array, columns=['x', 'y', 'z', 'time'])
        return dataframe, path

    def get_gesture_label(self, number):
        """
        取得手勢方向
        """
        # label_df = pd.read_csv("radar_data_csv/np_label.csv")
        # row = label_df.loc[label_df['filename'] == f"./radar_data/{self.npy_file_name}_{number}.npy"]
        label_df = pd.read_csv("radar_data_csv/np_label_storage.csv")
        row = label_df.loc[label_df['filename'] == f"/content/drive/MyDrive/Colab/radar_data/feng_data_{number}.npy"]
        if not row.empty:
            gesture_label = row['gesture'].values[0]
            return gesture_label
        else:
            return "Unknown"

    def plot_data_all(self, dataframe, number):
        """
        將數據以2D散點圖形式進行可視化並保存為PNG文件，並將三個子圖疊加成第四個圖形。
        """
        fig, axs = plt.subplots(2, 2, figsize=(16, 16))
        # point_size = 1000 * (np.arange(len(dataframe))+1)/len(dataframe)
        point_size = 500 

        # x, z 平面
        axs[0, 0].scatter(dataframe['x'], dataframe['z'], point_size)
        axs[0, 0].set_xlabel('X')
        axs[0, 0].set_ylabel('Z')
        axs[0, 0].set_xlim([0.6, -0.6])
        axs[0, 0].set_ylim([-0.6, 0.6])
        axs[0, 0].set_title(f"Front view (X-Z plane)")

        # x, y 平面
        axs[0, 1].scatter(dataframe['x'], dataframe['y'], point_size)
        axs[0, 1].set_xlabel('X')
        axs[0, 1].set_ylabel('Y')
        axs[0, 1].set_xlim([0.6, -0.6])
        axs[0, 1].set_ylim([1.2, 0])
        # axs[0, 1].set_xlim([1.2, -1.2])
        # axs[0, 1].set_ylim([2.4, 0])
        axs[0, 1].set_title(f"Top view (X-Y plane)")

        # y, z 平面
        axs[1, 0].scatter(dataframe['y'], dataframe['z'], point_size)
        axs[1, 0].set_xlabel('Y')
        axs[1, 0].set_ylabel('Z')
        axs[1, 0].set_xlim([0, 1.2])
        axs[1, 0].set_ylim([-0.6, 0.6])
        axs[1, 0].set_title(f"Left view (Y-Z plane)")

        # Doppler - Range
        axs[1, 1].scatter(dataframe['range'], dataframe['doppler'], point_size)
        axs[1, 1].set_xlabel('Range')
        axs[1, 1].set_ylabel('Doppler')
        axs[1, 1].set_xlim([0, 1.2])
        axs[1, 1].set_ylim([-2.4, 2.4])
        # axs[1, 1].set_xlim([-2.4, 2.4])
        # axs[1, 1].set_ylim([-4.8, 4.8])
        axs[1, 1].set_title(f"Doppler - Range")

        # 获取手势标签
        gesture_label = self.get_gesture_label(number)

        # 添加外层标题
        fig.suptitle(f"Gesture {number} - {gesture_label}")

        plt.tight_layout()
        plt.savefig(f"radar_data_png/Gesture.png")
        plt.close()

    def plot_data_2d(self, dataframe, number):
        """
        将数据以2D形式进行可视化并保存为PNG文件。
        """
        fig, axs = plt.subplots(1, 3, figsize=(18, 6))

        # x, z 平面
        axs[0].scatter(dataframe['x'], dataframe['z'], s=500)
        axs[0].set_xlabel('X')
        axs[0].set_ylabel('Z')
        axs[0].set_xlim([0.6, -0.6])
        axs[0].set_ylim([-0.6, 0.6])
        axs[0].set_title(f"Front view (X-Z plane)")

        # x, y 平面
        axs[1].scatter(dataframe['x'], dataframe['y'], s=500)
        axs[1].set_xlabel('X')
        axs[1].set_ylabel('Y')
        axs[1].set_xlim([0.6, -0.6])
        axs[1].set_ylim([1.2, 0])
        axs[1].set_title(f"Top view (X-Y plane)")

        # y, z 平面
        axs[2].scatter(dataframe['y'], dataframe['z'], s=500)
        axs[2].set_xlabel('Y')
        axs[2].set_ylabel('Z')
        axs[2].set_xlim([0, 1.2])
        axs[2].set_ylim([-0.6, 0.6])
        axs[2].set_title(f"Left view (Y-Z plane)")

        # 获取手势标签
        gesture_label = self.get_gesture_label(number)

        # 添加外层标题
        fig.suptitle(f"Gesture {number} - {gesture_label}")

        plt.tight_layout()
        plt.savefig(f"radar_data_png/Gesture.png")
        plt.close()

    def process_radar_data(self, number):
        gesture_dataframe, file_path = self.read_data(number)
        self.plot_data_all(gesture_dataframe, number)
        # self.plot_data_2d(gesture_dataframe, number)

        img = cv2.imread('radar_data_png/Gesture.png')
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image = cv2.bitwise_not(gray_img)

        if image is not None:
            roi_ranges = [
                ((130, 110), (730, 710)),    # ROI 1
                ((920, 110), (1520, 710)),   # ROI 2
                ((130, 900), (730, 1500)),   # ROI 3
                ((920, 900), (1520, 1500))   # ROI 4
            ]

            for roi_range in roi_ranges:
                roi_start = roi_range[0]
                roi_end = roi_range[1]
                cv2.rectangle(img, roi_start, roi_end, (0, 0, 255), 2)

            cv2.imshow('Gesture', img)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

            roi_resized = []
            for roi_range in roi_ranges:
                roi_start = roi_range[0]
                roi_end = roi_range[1]
                roi = image[roi_start[1]:roi_end[1], roi_start[0]:roi_end[0]]
                roi = cv2.dilate(roi, kernel, iterations=1)
                # cv2.imshow(f'ROI_{roi_range}', roi)
                roi_resized.append(cv2.resize(roi, (32, 32)))

            np.set_printoptions(threshold=np.inf)

            for i, roi in enumerate(roi_resized, start=1):
                _, roi = cv2.threshold(roi, 128, 255, cv2.THRESH_BINARY)
                # print("roi_resized:\n", roi)
                cv2.imwrite(f'radar_data_png/Resized_ROI{i}.png', roi)
            

            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print('無法讀取圖片')

if __name__ == '__main__':
    processor = RadarDataProcessor()
    file_number = input("請輸入檔案編號：")
    processor.process_radar_data(file_number)
