import os
import numpy as np
import matplotlib.pyplot as plt

def plot_data_from_npy(npy_folder, pic_folder):
    npy_files = [file for file in os.listdir(npy_folder) if file.endswith('.npy')]
    
    for npy_file in npy_files:
        file_path = os.path.join(npy_folder, npy_file)
        np_array = np.load(file_path)
        file_number = npy_file.split('_')[2].split('.')[0]
        plot_parameter_over_time(np_array, file_number, pic_folder)
        
def plot_parameter_over_time(np_array, number, pic_folder):
    y_ranges = {'Range': (-0.2, 0.8), 'Doppler': (-2.5, 2.5), 'Azimuth': (-60, 60), 'Elevation': (-60, 60)}
    param_indices = {'Range': 4, 'Doppler': 3, 'Azimuth': 6, 'Elevation': 7}
    
    background_color = (0.8, 0.8, 0.8)
    line_color = (0.2, 0.2, 0.2)
    
    for param, y_range in y_ranges.items():
        param_index = param_indices[param]
        times = np.arange(np_array.shape[0])
        values = np_array[:, param_index]

        plt.figure(figsize=(4, 4), facecolor=background_color)
        plt.plot(times, values, linewidth=3, color=line_color)
        plt.ylim(y_range)
        plt.axis('off')
        plt.gca().set_position([0, 0, 1, 1])
        plt.gca().set_aspect('auto')

        img_filename = f'{pic_folder}/yuan_data_{number}_{param.lower()}.png'
        plt.savefig(img_filename, dpi=80, bbox_inches='tight', pad_inches=0)
        plt.close()
        print(f"Image saved: {img_filename}")

npy_folder = 'radar_data'
pic_folder = 'radar_data_pic'

plot_data_from_npy(npy_folder, pic_folder)
