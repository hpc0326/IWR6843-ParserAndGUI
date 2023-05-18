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
        self.debug = False
        self.detection = 0
        self.num_tx_ant = 0
        self.max_buffer_size = 2**15
        self.byte_buffer = np.zeros(2**15, dtype='uint8')
        self.byte_buffer_length = 0
        self.magic_word = [2, 1, 4, 3, 6, 5, 8, 7]
        self.word = [1, 2**8, 2**16, 2**24]
        self.wave_start_pt = np.zeros((1, 3))
        self.wave_last_pt = np.zeros((1, 3))
        self.wave_end_pt = np.zeros((1, 3))
        self.wave_start_time = 0
        self.wave_end_time = 0
        self.tmp_record_arr = np.zeros((1, 4))
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
        if (self.byte_buffer_length + byteCount) < self.max_buffer_size:
            self.byte_buffer[self.byte_buffer_length:self.byte_buffer_length +
                    byteCount] = byteVec[:byteCount]
            self.byte_buffer_length = self.byte_buffer_length + byteCount

        # Check that the buffer has some data
        if self.byte_buffer_length > 16:

            # Check for all possible locations of the magic word
            possibleLocs = np.where(self.byte_buffer == self.magic_word[0])[0]

            # Confirm that is the beginning of the magic word and store the index in startIdx
            startIdx = []
            for loc in possibleLocs:
                check = self.byte_buffer[loc:loc+8]
                if np.all(check == self.magic_word):
                    startIdx.append(loc)

            # Check that startIdx is not empty
            if startIdx:

                # Remove the data before the first start index
                if startIdx[0] > 0 and startIdx[0] < self.byte_buffer_length:
                    self.byte_buffer[:self.byte_buffer_length-startIdx[0]
                            ] = self.byte_buffer[startIdx[0]:self.byte_buffer_length]
                    self.byte_buffer[self.byte_buffer_length-startIdx[0]:] = np.zeros(
                        len(self.byte_buffer[self.byte_buffer_length-startIdx[0]:]), dtype='uint8')
                    self.byte_buffer_length = self.byte_buffer_length - startIdx[0]

                # Check that there have no errors with the byte buffer length
                if self.byte_buffer_length < 0:
                    self.byte_buffer_length = 0

                # Read the total packet length
                totalPacketLen = np.matmul(self.byte_buffer[12:12+4], self.word)
                # Check that all the packet has been read
                if (self.byte_buffer_length >= totalPacketLen) and (self.byte_buffer_length != 0):
                    magicOK = 1
        
        # If magicOK is equal to 1 then process the message
        if magicOK:
            # Read the entire buffer
            readNumBytes = self.byte_buffer_length
            if (self.debug):
                print("readNumBytes: ", readNumBytes)
            allBinData = self.byte_buffer
            if (self.debug):
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
                    allBinData[totalBytesParsed::1], readNumBytes-totalBytesParsed, self.debug)

            if (self.debug):
                print("Parser result: ", parser_result)
            if (parser_result == 0):
                totalBytesParsed += (headerStartIndex+totalPacketNumBytes)
                numFramesParsed += 1

                if (self.debug):
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
            self.byte_buffer[:self.byte_buffer_length -
                    shiftSize] = self.byte_buffer[shiftSize:self.byte_buffer_length]
            self.byte_buffer[self.byte_buffer_length - shiftSize:] = np.zeros(
                len(self.byte_buffer[self.byte_buffer_length - shiftSize:]), dtype='uint8')
            self.byte_buffer_length = self.byte_buffer_length - shiftSize

            # Check that there are no errors with the buffer length
            if self.byte_buffer_length < 0:
                self.byte_buffer_length = 0
            # All processing done; Exit
            if (self.debug):
                print("numFramesParsed: ", numFramesParsed)

        return dataOK, frameNumber, detObj

    def find_average_point(self, data_ok, detection_obj):
        """ find average point """
        x_value = 0
        y_value = 0
        z_value = 0
        num_points = 0
        snr_max = 200
        zero_pt = np.zeros((1, 4))  # for initial zero value

        # get average point per frame
        if data_ok:
            pos_pt = np.zeros((detection_obj["numObj"], 4))
            avg_pt = zero_pt

            pos_pt = np.array(list(map(tuple, np.stack(
                [detection_obj["x"], detection_obj["y"], detection_obj["z"], detection_obj["snr"]], axis=1))))

            # 取出符合條件的索引
            indices = np.where(pos_pt[:, 3] > snr_max)

            # 取出對應的 x, y, z 值
            x_vals = pos_pt[indices, 0]
            y_vals = pos_pt[indices, 1]
            z_vals = pos_pt[indices, 2]

            # 計算平均值
            x_value = np.mean(x_vals)
            y_value = np.mean(y_vals)
            z_value = np.mean(z_vals)
            num_points += len(indices[0])

            if num_points > 0:
                avg_pt = np.array([[x_value, y_value, z_value, time.time()]])
                # print('avg_pt:', avg_pt)
                return avg_pt
                # print(pos_pt)
            else:
                avg_pt = zero_pt
                # print('avg_pt:', avg_pt)
                return avg_pt

    def point_record(self, data_ok, avg_pt, npy_file_dir, npy_file_name, direction):
        """ record gesture point"""
        zero_pt = np.zeros((1, 4))  # for initial zero value

        # update start_detect flag
        if data_ok:
            self.detection = self.detection + 1

        # start record
        if data_ok and (avg_pt != zero_pt).all():
            if self.detection == 1:
                print("DETECTION START")
                self.wave_start_time = time.time()
                self.tmp_record_arr = avg_pt
                self.wave_start_pt = avg_pt

            self.wave_last_pt = self.wave_end_pt
            self.wave_end_pt = avg_pt

            if (self.wave_end_pt != self.wave_last_pt).all():  # avoid noise point
                if self.detection != 1:  # avoid duplicate start point
                    self.tmp_record_arr = np.append(self.tmp_record_arr, avg_pt, axis=0)

        elif data_ok == 0:
            self.wave_end_time = time.time()
            wave_time = self.wave_end_time - self.wave_start_time
            if wave_time > 3:
                # every time execute only can choose one of leftright or updown or others
                # left / right detect
                if direction == 0:
                    if self.wave_end_pt[0][0] > self.wave_start_pt[0][0]:
                        print("left wave")
                        filecount = len(os.listdir(npy_file_dir))
                        filename = f"./radar_data/{npy_file_name}_{filecount}.npy"
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('radar_data_csv/np_label.csv', 'a+', newline='', encoding='utf-8') as csvfile:
                            demo_writer = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demo_writer.writerow([filename, "left wave"])
                        self.tmp_record_arr = zero_pt
                    elif self.wave_end_pt[0][0] < self.wave_start_pt[0][0]:
                        print("right wave")
                        filecount = len(os.listdir(npy_file_dir))
                        filename = f"./radar_data/{npy_file_name}_{filecount}.npy"
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('radar_data_csv/np_label.csv', 'a+', newline='', encoding='utf-8') as csvfile:
                            demo_writer = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demo_writer.writerow([filename, "right wave"])
                        self.tmp_record_arr = zero_pt
                
                # up / down detect
                if direction == 1:
                    if self.wave_end_pt[0][2] > self.wave_start_pt[0][2]:
                        print("up wave")
                        filecount = len(os.listdir(npy_file_dir))
                        filename = f"./radar_data/{npy_file_name}_{filecount}.npy"
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('radar_data_csv/np_label.csv', 'a+', newline='', encoding='utf-8') as csvfile:
                            demo_writer = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demo_writer.writerow([filename, "up wave"])
                        self.tmp_record_arr = zero_pt

                    elif self.wave_end_pt[0][2] < self.wave_start_pt[0][2]:
                        print("down wave")
                        filecount = len(os.listdir(npy_file_dir))
                        filename = f"./radar_data/{npy_file_name}_{filecount}.npy"
                        new_arr = self.change_time_unit(self.tmp_record_arr)
                        np.save(filename, new_arr)
                        with open('radar_data_csv/np_label.csv', 'a+', newline='', encoding='utf-8') as csvfile:
                            demo_writer = csv.writer(
                                csvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demo_writer.writerow([filename, "down wave"])
                        self.tmp_record_arr = zero_pt

                # others detect
                if direction == 2:
                    if (self.wave_end_pt != self.wave_start_pt).all():
                        print("others")
                        with open('radar_data_csv/np_label.csv', 'a+', newline='', encoding='utf-8') as democsvfile:
                            demo_output_writer = csv.writer(democsvfile, delimiter=',', quotechar='', quoting=csv.QUOTE_NONE)
                            demo_output_writer.writerow(["others"])

                self.detection = 0
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
