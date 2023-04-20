""" module radar """
import time
import serial
import numpy as np
from modules.ti_radar_sdk import parser_one_mmw_demo_output_packet


class Radar:
    """ Class: Radar """

    def __init__(self):
        self.num_tx_ant = 0
        self.start_index = 0
        self.end_index = 0
        self.max_buffer_size = 2**15
        self.radar_data_buffer = np.zeros(self.max_buffer_size, dtype='uint8')
        self.magic_word = [2, 1, 4, 3, 6, 5, 8, 7]
        self.magic_flag = False
        self.word = [1, 2**8, 2**16, 2**24]
        print('''[Info] Initialize Radar class ''')

    def start(self, radar_cli_port, radar_data_port, radar_config_file_path):
        """ Radar.start """
        radar_config = []

        cli_serial = serial.Serial(radar_cli_port, 115200)
        data_serial = serial.Serial(radar_data_port, 921600)
        # Read the configuration file and send it to the board
        with open(radar_config_file_path, encoding='utf-8') as radar_config_file:
            for line in radar_config_file:
                radar_config.append(line.rstrip('\r\n'))
        # Write the radar configuration to the radar device
        for line in radar_config:
            cli_serial.write((line+'\n').encode())
            time.sleep(0.01)

        self.parse_radar_config(radar_config)
        print('''[Info] Radar device starting''')
        return cli_serial, data_serial

    def parse_radar_config(self, radar_config):
        """ Parsing radar config """
        radar_parameters = {}

        for line in radar_config:
            line_split = line.split(" ")
            if line_split[0] == 'profileCfg':
                start_freq = int(float(line_split[2]))
                idle_time = int(line_split[3])
                ramp_end_time = float(line_split[5])
                freq_slope_const = float(line_split[8])
                num_adc_samples = int(line_split[10])
                num_adc_aamples_round_to_2 = 1
                while num_adc_samples > num_adc_aamples_round_to_2:
                    num_adc_aamples_round_to_2 = num_adc_aamples_round_to_2 * 2
                dig_out_sample_rate = int(line_split[11])
            if line_split[0] == 'frameCfg':
                chirp_start_idx = int(line_split[1])
                chirp_end_idx = int(line_split[2])
                num_loops = float(line_split[3])
                frame_periodicity = float(line_split[5])
                num_frames = 1000/frame_periodicity
            if line_split[0] == 'chirpCfg':
                self.num_tx_ant = self.num_tx_ant + 1

        num_chirps_per_frame = (
            chirp_end_idx - chirp_start_idx + 1) * num_loops
        radar_parameters["num_frames"] = num_frames
        radar_parameters["num_doppler_bins"] = num_chirps_per_frame / self.num_tx_ant
        radar_parameters["num_range_bins"] = num_adc_aamples_round_to_2
        radar_parameters["range_resolution_meters"] = (
            3e8 * dig_out_sample_rate * 1e3) / (2 * freq_slope_const * 1e12 * num_adc_samples)
        radar_parameters["range_idx_to_meters"] = (3e8 * dig_out_sample_rate * 1e3) / (
            2 * freq_slope_const * 1e12 * radar_parameters["num_doppler_bins"])
        radar_parameters["doppler_resolution_mps"] = 3e8 / (2 * start_freq * 1e9 * (
            idle_time + ramp_end_time) * 1e-6 * radar_parameters["num_doppler_bins"] * self.num_tx_ant)
        radar_parameters["max_range"] = (
            300 * 0.9 * dig_out_sample_rate)/(2 * freq_slope_const * 1e3)
        radar_parameters["max_velocity"] = 3e8 / \
            (4 * start_freq * 1e9 * (idle_time + ramp_end_time) * 1e-6 * self.num_tx_ant)
        radar_parameters["frame_periodicity"] = frame_periodicity
        print(
            f'''[Info] radar_parameters: {radar_parameters} ''')
        return radar_parameters

    def read_and_parse_radar_data(self, data_serial):
        ''' read_and_parse_data '''
        # 讀取雷達數據
        radar_data = data_serial.read(data_serial.in_waiting)
        radar_data_np = np.frombuffer(radar_data, dtype='uint8')
        radar_data_lenth = len(radar_data_np)
        # 將數據添加到緩存區
        self.end_index = self.end_index + radar_data_lenth
        if self.end_index < self.max_buffer_size:
            # 確保radar_data_np和self.radar_data_buffer尺寸一致
            if self.end_index + radar_data_lenth > self.max_buffer_size:
                radar_data_lenth = self.max_buffer_size - self.end_index
                radar_data_np = radar_data_np[:radar_data_lenth]
                self.radar_data_buffer[self.start_index:self.end_index] = radar_data_np[:]
        # 大於16個字節，才開始檢查檢查緩存區是否有數據
        if self.end_index > 16:
            # 查找魔術字節的所有可能位置
            possible_locs = np.where(
                self.radar_data_buffer == self.magic_word[0])[0]
            # 確定魔術字節的開始位置，並將其儲存到start_idx
            start_idx = []
            for loc in possible_locs:
                check = self.radar_data_buffer[loc:loc+8]
                if np.all(check == self.magic_word):  # 都符合magic number
                    start_idx.append(loc)
            # 檢查start_idx是否為空
            if start_idx:
                # 移除第一個魔術字節之前的數據
                if start_idx[0] > 0:
                    if start_idx[0] < self.end_index:
                        self.radar_data_buffer[:self.end_index-start_idx[0]
                                               ] = self.radar_data_buffer[start_idx[0]:self.end_index]
                        self.radar_data_buffer[self.end_index-start_idx[0]:] = np.zeros(
                            len(self.radar_data_buffer[self.end_index-start_idx[0]:]), dtype='uint8')
                        self.end_index = self.end_index - start_idx[0]
                # 確認緩衝區長度沒有錯誤
                self.end_index = max(self.end_index, 0)
                # 讀取數據包的總長度
                total_packet_len = np.matmul(
                    self.radar_data_buffer[12:16], self.word)
                # 檢查是否已讀取整個數據包
                if self.end_index >= total_packet_len:
                    if self.end_index != 0:
                        self.magic_flag = True
        # 如果 magic_flag 為 True，則處理消息
        if self.magic_flag:
            # 讀取整個緩衝區
            print(f'''radar_data_lenth: {radar_data_lenth}''')
            print(f'''radar_data_buffer: {self.radar_data_buffer} ''')

            # init local variables
            start_idx = 0
            numFramesParsed = 0
            DEBUG = True

            parser_result, \
                headerStartIndex,  \
                totalPacketNumBytes, \
                numDetObj,  \
                numTlv,  \
                subFrameNumber,  \
                detectedX_array,  \
                detectedY_array,  \
                detectedZ_array,  \
                detectedV_array,  \
                detectedRange_array,  \
                detectedAzimuth_array,  \
                detectedElevation_array,  \
                detectedSNR_array,  \
                detectedNoise_array = parser_one_mmw_demo_output_packet(
                    self.radar_data_buffer[::], self.end_index, DEBUG)

            detObj = {
                "numObj": numDetObj,
                "range": detectedRange_array,
                "x": detectedX_array,
                "y": detectedY_array,
                "z": detectedZ_array,
                "elevation": detectedElevation_array,
                "snr": detectedSNR_array
            }
            print(detObj)
