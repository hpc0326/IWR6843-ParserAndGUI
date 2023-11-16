import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

load_dotenv()
npy_file_name = os.getenv("DATA_STORAGE_FILE_NAME")

class ProcessingThread(threading.Thread):
    def __init__(self, radar_viz, file_number):
        threading.Thread.__init__(self)
        self.radar_viz = radar_viz
        self.file_number = file_number

    def run(self):
        self.radar_viz.process_new_file(self.file_number)

class RadarDataVisualization:
    def __init__(self):
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
        self.axes.view_init(elev=10, azim=-90)
        # self.axes.view_init(elev=10, azim=180)  
        plt.title(title)

    def update_plot(self, frame):
        snr_nonzero_indices = np.nonzero(self.gesture_dataframe['snr'][:frame+1].values)[0]
        self.scatter._offsets3d = (
            self.gesture_dataframe['x'][:frame+1].values[snr_nonzero_indices],
            self.gesture_dataframe['y'][:frame+1].values[snr_nonzero_indices],
            self.gesture_dataframe['z'][:frame+1].values[snr_nonzero_indices]
        )
        # self.scatter.set_array(range(len(snr_nonzero_indices)))
        # self.scatter.set_cmap('plasma')
        # self.scatter.set_clim(0, len(snr_nonzero_indices))
        return self.scatter,

    def process_new_file(self, file_number):
        self.gesture_dataframe, self.file_path = self.read_data(file_number)
        print(self.gesture_dataframe)
        self.gesture_dataframe = self.gesture_dataframe.loc[self.gesture_dataframe['snr'] != 0].reset_index(drop=True)
        # print(self.gesture_dataframe)

        self.set_figure(f'Filepath: {self.file_path}')
        animation = FuncAnimation(self.fig, self.update_plot, frames=len(self.gesture_dataframe), interval=40, blit=True)

        output_file = 'radar_data_gif/PointCloud_animation.gif'
        animation.save(output_file, writer='pillow')
        print(f"圖片已儲存至 {output_file}")

    def watch_directory(self, directory):
        event_handler = FileSystemEventHandler()

        def on_created(event):
            if not event.is_directory:
                file_name = event.src_path
                file_number = file_name.split('_')[-1].split('.')[0]
                processing_thread = ProcessingThread(self, file_number)
                processing_thread.start()

        event_handler.on_created = on_created

        observer = Observer()
        observer.schedule(event_handler, directory, recursive=False)
        observer.start()
        try:
            while True:
                pass
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == '__main__':
    radar_viz = RadarDataVisualization()
    radar_viz.watch_directory('radar_data')
