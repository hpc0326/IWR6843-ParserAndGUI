"""This module contains the main application logic for processing and displaying radar data."""
from threading import Thread
from modules.utils import Utils
from modules.radar import Radar
from modules.gui import GUI
from modules.heatmap import HEATMAP
import numpy as np

# Point Cloud GUI
POINT_CLOUD_GUI = 0
# Heatmap GUI
HEATMAP_GUI = 0

# Initialize classes
Utils = Utils()
Radar = Radar()
GUI = GUI()
HEATMAP = HEATMAP()

RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, IMAGE_STORAGE_FILE_PATH = Utils.get_radar_env()
cli_serial, data_serial = Radar.start(
    RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH)

RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE = Utils.get_gui_env()


def sliding_window(frameNum, queue, snr):

    queue.append(snr)

    # Check if the window buffer is full
    if len(queue) >= frameNum:
        # Clear the window buffer for the next window
        queue = queue[1:]  # Remove the oldest data point

    return queue


def trigger_check(sta, lta, status):
    if not sta or not lta:
        return status

    staMean = sum(sta)/len(sta)
    ltaMean = sum(lta)/len(lta)

    if staMean/ltaMean > 1.35:
        status = True
    elif staMean/ltaMean < 1.1:
        status = False

    # print(f'''status: {status}, STA/LTA: {staMean/ltaMean}, staMean:{staMean}, ltaMean:{ltaMean}''')
    return status


def radar_thread_function():
    """radar_thread_function"""
    sta = []
    lta = []
    status = False
    prev_status = False  # 新增变量以跟踪上一个状态
    counter = 0
    pre_trigger_data = []

    while True:
        data_ok, _, detection_obj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(data_ok, detection_obj)

        if data_ok:
            pre_trigger_data.append(avg_pt)
            if len(pre_trigger_data) > 10:
                pre_trigger_data.pop(0)

            # trigger checking
            prev_status = status
            status = trigger_check(sta, lta, status)
            if status:
                if not prev_status:
                    print("\nGesture Start")
                    for data in pre_trigger_data:
                        Radar.sliding_window(data)
                    counter = len(pre_trigger_data)

            if status and counter < 25:
                Radar.sliding_window(avg_pt)
                counter += 1
                print(f'''Record frame {counter}, data: {avg_pt}''')

            if status and counter == 25:
                print("Gesture End\n")
                Radar.data_to_numpy(DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, IMAGE_STORAGE_FILE_PATH)
                # reset
                counter = 0
                sta = []
                lta = []
                status = False
                pre_trigger_data = []
                Radar.window_buffer = np.ndarray((0, 9))

            if not status:
                snr = avg_pt[0][5]
                sta = sliding_window(15, sta, snr + 150)
                lta = sliding_window(35, lta, snr + 150)

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
