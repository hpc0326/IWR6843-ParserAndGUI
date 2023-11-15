"""This module contains the main application logic for processing and displaying radar data."""
from threading import Thread
from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
from modules.heatmap import HEATMAP
import time
import numpy as np
from threading import Thread
import csv

# 0: left / right detection; 1: up / down detection; 2: other detection
DETECT_DIRECTION = 0
#Point Cloud GUI
POINT_CLOUD_GUI = 0
#Heatmap GUI
HEATMAP_GUI = 0

# Initialize classes
Utils = Utils()
Radar = Radar()
GUI = GUI()
HEATMAP = HEATMAP()

RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME = Utils.get_radar_env()
cli_serial, data_serial = Radar.start(
    RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH)

RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE = Utils.get_gui_env()


def SliWin(frameNum, queue, snr):

    queue.append(snr)
     
    # Check if the window buffer is full
    if len(queue) >= frameNum:
        # Clear the window buffer for the next window
        queue = queue[1:]  # Remove the oldest data point

    return queue 

def triggerCheck(sta, lta, status):

    staMean = sum(sta)/len(sta)
    ltaMean = sum(lta)/len(lta)

    if staMean/ltaMean > 1.1 : #adjust the trigger threshold by yourself
        status = True
    elif staMean/ltaMean < 0.1:
        status = False
    # print(staMean/ltaMean)
    print(f'''status: {status}, STA/LTA: {staMean/ltaMean}''')
    return status

def radar_thread_function():
    """radar_thread_function"""
    sta = []
    lta = []
    status = False
    counter = 0
    
    while True:
        data_ok, _, detection_obj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(data_ok, detection_obj)
        
        if data_ok and status == True and counter < 25:

            #append each avg_pt
            Radar.sliding_window(avg_pt)
            counter += 1
            print(f"Record frame {counter}")
        
        elif data_ok and status == True and counter == 25:
            # print('avg', avg_pt)
            #write to csv
            Radar.data_to_csv()
            #save data
            print("Gesture End\n")
            Radar.data_to_numpy(
                DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME)
            
            #reset
            counter = 0
            sta = []
            lta = []
            status = False
            Radar.window_buffer = np.ndarray((0,9))
            

        elif data_ok:
            #trigger data type
            snr = avg_pt[0][5]
            sta = SliWin(15, sta, snr)
            lta = SliWin(35, lta, snr)
            # print(snr)

            #trigger checking
            status = triggerCheck(sta, lta, status)
            if (status):
                print("\nGesture Start")
            
  
        if data_ok and POINT_CLOUD_GUI and not HEATMAP_GUI:
            GUI.store_point(avg_pt[:, :3])
            
        if data_ok and HEATMAP_GUI and not POINT_CLOUD_GUI:
            HEATMAP.save_data(detection_obj['doppler'], detection_obj['range'])

if POINT_CLOUD_GUI:
    thread1 = Thread(target=radar_thread_function, args=(), daemon=True)
    thread1.start()
    GUI.start(RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE)
else:
    radar_thread_function()

if HEATMAP_GUI:
    thread2 = Thread(target=radar_thread_function, args=(), daemon=True)
    thread2.start()
    HEATMAP.start()

