""" module radar """
import os
import time
import csv
import serial
import numpy as np
from modules.parser_mmw_demo import parser_one_mmw_demo_output_packet
# from modules.ti_radar_sdk import parser_one_mmw_demo_output_packet


class Radar:
    """ Class: Radar """
    def __init__(self):
        self.DEBUG = False
        self.DETECTION = 0
        self.maxBufferSize = 2**15
        self.CLIport = {}
        self.Dataport = {}
        self.byteBuffer = np.zeros(2**15, dtype='uint8')
        self.byteBufferLength = 0
        self.magicWord = [2, 1, 4, 3, 6, 5, 8, 7]
        self.frameData = {}
        self.currentIndex = 0
        self.point = np.zeros((50, 3))
        self.word = [1, 2**8, 2**16, 2**24]
        self.wave_start_pt = np.zeros((1, 3))
        self.wave_last_pt = np.zeros((1, 3))
        self.wave_end_pt = np.zeros((1, 3))
        self.wave_start_time = 0
        self.wave_end_time = 0
        self.tmp_record_arr = np.zeros((1, 4))

        self.start_index = 0
        self.num_tx_ant = 0
        self.start_index = 0
        self.end_index = 0
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
        """ read and parse radar data """
        # Initialize variables
        magicOK = 0  # Checks if magic number has been read
        dataOK = 0  # Checks if the data has been read correctly
        frameNumber = 0
        detObj = {}

        readBuffer = data_serial.read(data_serial.in_waiting)
        byteVec = np.frombuffer(readBuffer, dtype='uint8')
        byteCount = len(byteVec)

        # Check that the buffer is not full, and then add the data to the buffer
        if (self.byteBufferLength + byteCount) < self.maxBufferSize:
            self.byteBuffer[self.byteBufferLength:self.byteBufferLength +
                    byteCount] = byteVec[:byteCount]
            self.byteBufferLength = self.byteBufferLength + byteCount

        # Check that the buffer has some data
        if self.byteBufferLength > 16:

            # Check for all possible locations of the magic word
            possibleLocs = np.where(self.byteBuffer == self.magicWord[0])[0]

            # Confirm that is the beginning of the magic word and store the index in startIdx
            startIdx = []
            for loc in possibleLocs:
                check = self.byteBuffer[loc:loc+8]
                if np.all(check == self.magicWord):
                    startIdx.append(loc)

            # Check that startIdx is not empty
            if startIdx:

                # Remove the data before the first start index
                if startIdx[0] > 0 and startIdx[0] < self.byteBufferLength:
                    self.byteBuffer[:self.byteBufferLength-startIdx[0]
                            ] = self.byteBuffer[startIdx[0]:self.byteBufferLength]
                    self.byteBuffer[self.byteBufferLength-startIdx[0]:] = np.zeros(
                        len(self.byteBuffer[self.byteBufferLength-startIdx[0]:]), dtype='uint8')
                    self.byteBufferLength = self.byteBufferLength - startIdx[0]

                # Check that there have no errors with the byte buffer length
                if self.byteBufferLength < 0:
                    self.byteBufferLength = 0

                # Read the total packet length
                totalPacketLen = np.matmul(self.byteBuffer[12:12+4], self.word)
                # Check that all the packet has been read
                if (self.byteBufferLength >= totalPacketLen) and (self.byteBufferLength != 0):
                    magicOK = 1
        
        # If magicOK is equal to 1 then process the message
        if magicOK:
            # Read the entire buffer
            readNumBytes = self.byteBufferLength
            if (self.DEBUG):
                print("readNumBytes: ", readNumBytes)
            allBinData = self.byteBuffer
            if (self.DEBUG):
                print("allBinData: ",
                    allBinData[0], allBinData[1], allBinData[2], allBinData[3])

            # init local variables
            totalBytesParsed = 0
            numFramesParsed = 0

            # parser_one_mmw_demo_output_packet extracts only one complete frame at a time
            # so call this in a loop till end of file
            #
            # parser_one_mmw_demo_output_packet function already prints the
            # parsed data to stdio. So showcasing only saving the data to arrays
            # here for further custom processing
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
                    allBinData[totalBytesParsed::1], readNumBytes-totalBytesParsed, self.DEBUG)

            if (self.DEBUG):
                print("Parser result: ", parser_result)
            if (parser_result == 0):
                totalBytesParsed += (headerStartIndex+totalPacketNumBytes)
                numFramesParsed += 1

                if (self.DEBUG):
                    print("totalBytesParsed: ", totalBytesParsed)
                ##################################################################################
                # TODO: use the arrays returned by above parser as needed.
                # For array dimensions, see help(parser_one_mmw_demo_output_packet)
                # help(parser_one_mmw_demo_output_packet)
                ##################################################################################

                detObj = {"numObj": numDetObj, "range": detectedRange_array,
                        "x": detectedX_array, "y": detectedY_array, "z": detectedZ_array,
                        "elevation": detectedElevation_array, "snr": detectedSNR_array
                        }

                detSideInfoObj = {"doppler": detectedV_array, "snr": detectedSNR_array,
                                "noise": detectedNoise_array
                                }
                dataOK = 1

            shiftSize = totalPacketNumBytes
            self.byteBuffer[:self.byteBufferLength -
                    shiftSize] = self.byteBuffer[shiftSize:self.byteBufferLength]
            self.byteBuffer[self.byteBufferLength - shiftSize:] = np.zeros(
                len(self.byteBuffer[self.byteBufferLength - shiftSize:]), dtype='uint8')
            self.byteBufferLength = self.byteBufferLength - shiftSize

            # Check that there are no errors with the buffer length
            if self.byteBufferLength < 0:
                self.byteBufferLength = 0
            # All processing done; Exit
            if (self.DEBUG):
                print("numFramesParsed: ", numFramesParsed)

        return dataOK, frameNumber, detObj

    def find_average_point(self, dataOk, detObj):
        """ find average point """
        x = 0
        y = 0
        z = 0
        n = 0
        snr_max = 200
        zero_pt = np.zeros((1, 4))  # for initial zero value

        # get average point per frame
        if dataOk:
            pos_pt = np.zeros((detObj["numObj"], 4))
            avg_pt = zero_pt

            pos_pt = np.array(list(map(tuple, np.stack(
                [detObj["x"], detObj["y"], detObj["z"], detObj["snr"]], axis=1))))

            # 取出符合條件的索引
            indices = np.where(pos_pt[:, 3] > snr_max)

            # 取出對應的 x, y, z 值
            x_vals = pos_pt[indices, 0]
            y_vals = pos_pt[indices, 1]
            z_vals = pos_pt[indices, 2]

            # 計算平均值
            x = np.mean(x_vals)
            y = np.mean(y_vals)
            z = np.mean(z_vals)
            n += len(indices[0])

            if n > 0:
                avg_pt = np.array([[x, y, z, time.time()]])
                print('avg_pt:', avg_pt)
                return avg_pt
                # print(pos_pt)
            else:
                avg_pt = zero_pt
                print('avg_pt:', avg_pt)
                return avg_pt

    def point_record(self, dataOk, avg_pt, dir, direction):
        """ record gesture point"""
        zero_pt = np.zeros((1, 4))  # for initial zero value

        # update start_detect flag
        if dataOk:
            self.DETECTION = self.DETECTION + 1

        # start record
        if dataOk and (avg_pt != zero_pt).all():
            if self.DETECTION == 1:
                print("DETECTION START")
                self.wave_start_time = time.time()
                self.tmp_record_arr = avg_pt
                self.wave_start_pt = avg_pt

            self.wave_last_pt = self.wave_end_pt
            self.wave_end_pt = avg_pt

            if (self.wave_end_pt != self.wave_last_pt).all():  # avoid noise point
                if self.DETECTION != 1:  # avoid duplicate start point
                    self.tmp_record_arr = np.append(self.tmp_record_arr, avg_pt, axis=0)

        elif dataOk == 0:
            self.wave_end_time = time.time()
            wave_time = self.wave_end_time - self.wave_start_time
            if wave_time > 3:
                # every time execute only can choose one of leftright or updown or others
                # left / right detect
                if direction == 0:
                    if self.wave_end_pt[0][0] > self.wave_start_pt[0][0]:
                        print("left wave")
                        filecount = len(os.listdir(dir))
                        filename = "./radar_data/feng_data_{}.npy".format(
                            filecount)
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('np_label.csv', 'a+', newline='') as csvfile:
                            demoWriter = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demoWriter.writerow([filename, "left wave"])
                        self.tmp_record_arr = zero_pt
                    elif self.wave_end_pt[0][0] < self.wave_start_pt[0][0]:
                        print("right wave")
                        filecount = len(os.listdir(dir))
                        filename = "./radar_data/feng_data_{}.npy".format(
                            filecount)
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('np_label.csv', 'a+', newline='') as csvfile:
                            demoWriter = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demoWriter.writerow([filename, "right wave"])
                        self.tmp_record_arr = zero_pt
                
                # up / down detect
                if direction == 1:
                    if self.wave_end_pt[0][2] > self.wave_start_pt[0][2]:
                        print("up wave")
                        filecount = len(os.listdir(dir))
                        filename = "./radar_data/feng_data_{}.npy".format(filecount)
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('np_label.csv', 'a+', newline='') as csvfile:
                            demoWriter = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demoWriter.writerow([filename, "up wave"])
                        self.tmp_record_arr = zero_pt

                    elif self.wave_end_pt[0][2] < self.wave_start_pt[0][2]:
                        print("down wave")
                        filecount = len(os.listdir(dir))
                        filename = "./radar_data/feng_data_{}.npy".format(filecount)
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('np_label.csv', 'a+', newline='') as csvfile:
                            demoWriter = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demoWriter.writerow([filename, "down wave"])
                        self.tmp_record_arr = zero_pt
                
                # others detect
                if direction == 2:
                    if (self.wave_end_pt != self.wave_start_pt).all():
                        print("others")
                        with open('mmw_demo_output.csv', 'a+', newline='') as democsvfile:
                            demoOutputWriter = csv.writer(democsvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demoOutputWriter.writerow(["others"])

                self.DETECTION = 0
                self.wave_start_pt = zero_pt
                self.wave_last_pt = zero_pt
                self.wave_end_pt = zero_pt

    def change_time_unit(self, tmp_arr):
        """ change time unit """
        stime = tmp_arr[0][3]
        new_arr = tmp_arr
        arr_len = len(tmp_arr)

        for i in range(arr_len):
            new_arr[i][3] = new_arr[i][3] - stime
        return new_arr
    
    # def read_and_parse_radar_data(self, data_serial):
    #     ''' read_and_parse_data '''
    #     # 讀取雷達數據
    #     radar_data = data_serial.read(data_serial.in_waiting)
    #     radar_data_np = np.frombuffer(radar_data, dtype='uint8')
    #     radar_data_lenth = len(radar_data_np)
    #     # 將數據添加到緩存區
    #     self.end_index = self.end_index + radar_data_lenth
    #     if self.end_index < self.max_buffer_size:
    #         # 確保radar_data_np和self.radar_data_buffer尺寸一致
    #         if self.end_index + radar_data_lenth > self.max_buffer_size:
    #             radar_data_lenth = self.max_buffer_size - self.end_index
    #             radar_data_np = radar_data_np[:radar_data_lenth]
    #             self.radar_data_buffer[self.start_index:self.end_index] = radar_data_np[:]
    #     # 大於16個字節，才開始檢查檢查緩存區是否有數據
    #     if self.end_index > 16:
    #         # 查找魔術字節的所有可能位置
    #         possible_locs = np.where(
    #             self.radar_data_buffer == self.magic_word[0])[0]
    #         # 確定魔術字節的開始位置，並將其儲存到start_idx
    #         start_idx = []
    #         for loc in possible_locs:
    #             check = self.radar_data_buffer[loc:loc+8]
    #             if np.all(check == self.magic_word):  # 都符合magic number
    #                 start_idx.append(loc)
    #         # 檢查start_idx是否為空
    #         if start_idx:
    #             # 移除第一個魔術字節之前的數據
    #             if start_idx[0] > 0:
    #                 if start_idx[0] < self.end_index:
    #                     self.radar_data_buffer[:self.end_index-start_idx[0]
    #                                            ] = self.radar_data_buffer[start_idx[0]:self.end_index]
    #                     self.radar_data_buffer[self.end_index-start_idx[0]:] = np.zeros(
    #                         len(self.radar_data_buffer[self.end_index-start_idx[0]:]), dtype='uint8')
    #                     self.end_index = self.end_index - start_idx[0]
    #             # 確認緩衝區長度沒有錯誤
    #             self.end_index = max(self.end_index, 0)
    #             # 讀取數據包的總長度
    #             total_packet_len = np.matmul(
    #                 self.radar_data_buffer[12:16], self.word)
    #             # 檢查是否已讀取整個數據包
    #             if self.end_index >= total_packet_len:
    #                 if self.end_index != 0:
    #                     self.magic_flag = True
    #     # 如果 magic_flag 為 True，則處理消息
    #     if self.magic_flag:
    #         # 讀取整個緩衝區
    #         print(f'''radar_data_lenth: {radar_data_lenth}''')
    #         print(f'''radar_data_buffer: {self.radar_data_buffer} ''')

    #         # init local variables
    #         start_idx = 0
    #         numFramesParsed = 0
    #         DEBUG = True

    #         parser_result, \
    #             headerStartIndex,  \
    #             totalPacketNumBytes, \
    #             numDetObj,  \
    #             numTlv,  \
    #             subFrameNumber,  \
    #             detectedX_array,  \
    #             detectedY_array,  \
    #             detectedZ_array,  \
    #             detectedV_array,  \
    #             detectedRange_array,  \
    #             detectedAzimuth_array,  \
    #             detectedElevation_array,  \
    #             detectedSNR_array,  \
    #             detectedNoise_array = parser_one_mmw_demo_output_packet(
    #                 self.radar_data_buffer[::], self.end_index, DEBUG)

    #         detObj = {
    #             "numObj": numDetObj,
    #             "range": detectedRange_array,
    #             "x": detectedX_array,
    #             "y": detectedY_array,
    #             "z": detectedZ_array,
    #             "elevation": detectedElevation_array,
    #             "snr": detectedSNR_array
    #         }
    #         print(detObj)
    
    