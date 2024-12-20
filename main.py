"""This module contains the main application logic for processing and displaying radar data."""
from threading import Thread
from modules.utils import POINT_CLOUD_GUI_ENV, Radar_ENV
from modules.radar import Radar
from modules.point_cloud import Point_Cloud
from modules.heatmap import Heat_Map
from modules.trigger_tool import Trigger
import numpy as np

# Point Cloud GUI
# GUI Type 
# 0: no gui
# 1: POINT_CLOUD
# 2: HEATMAP
# 3: ALL GUI
GUI_TYPE=0
WINDOW_LENGTH=25

# Initialize classes
radar_env = Radar_ENV()
Radar = Radar()
PointCloud = Point_Cloud()
HeatMap = Heat_Map()
Trigger = Trigger()

cli_serial, data_serial = Radar.start(
    radar_env.radar_cli_port, 
    radar_env.radar_data_port, 
    radar_env.radar_config_file_path)


def radar_thread_function():
    """radar_thread_function"""
    status = False
    prev_status = False  # 新增变量以跟踪上一个状态
    counter = 0
    print("start radar_thread_function")

    while True:
        data_ok, _, detection_obj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(data_ok, detection_obj)
        
        if data_ok:
            Trigger.data_buffer.append(avg_pt)
            
            if len(Trigger.data_buffer) > 10:
                Trigger.data_buffer.pop(0)

            # trigger checking
            prev_status = status
            status = Trigger.trigger_check(status)
            
            if status:
                
                if not prev_status:
                    print("\nGesture Start")
                    for data in Trigger.data_buffer:
                        Radar.sliding_window(data)
                    counter = len(Trigger.data_buffer)

                if counter < WINDOW_LENGTH:
                    Radar.sliding_window(avg_pt)
                    counter += 1
                    print(f'''Record frame {counter}, data: {avg_pt}''')

                if  counter == WINDOW_LENGTH:
                    print("Gesture End\n")
                    # Radar.data_to_numpy(
                    #     radar_env.data_storage_file_path, 
                    #     radar_env.data_storage_file_name, 
                    #     radar_env.pic_storage_file_name)
                    # reset
                    Trigger.param_reset()
                    counter = 0
                    status = False
                    Radar.window_buffer = np.ndarray((0, 9))

            if not status:
                snr = avg_pt[0][5]
                Trigger.sliding_window(15, 35, snr + 150)

        if data_ok and GUI_TYPE==1:
            PointCloud.store_point(avg_pt[:, :3])

        if data_ok and GUI_TYPE==2:
            HeatMap.save_data(detection_obj['doppler'], detection_obj['range'])




if __name__ == "__main__": 
    
    if GUI_TYPE==1:
        thread1 = Thread(target=radar_thread_function, args=(), daemon=True)
        thread1.start()
        pc_env = POINT_CLOUD_GUI_ENV()
        PointCloud.start(
            pc_env.radar_position_x, 
            pc_env.radar_position_y, 
            pc_env.radar_position_z, 
            pc_env.grid_size)
    elif GUI_TYPE==2:
        thread2 = Thread(target=radar_thread_function, args=(), daemon=True)
        thread2.start()
        HeatMap.start()
    else:
        radar_thread_function()