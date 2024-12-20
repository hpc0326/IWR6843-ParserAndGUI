""" module radar """
import os
import time
import csv
import serial
import numpy as np
import pandas as pd
from modules.parser_module.parser_mmw_demo import parser_one_mmw_demo_output_packet
import matplotlib.pyplot as plt


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
        self.radar_parameters = {}
        # Number of data points in each window
        # Buffer to store data points for each window
        self.window_buffer = np.ndarray((0, 9))
        self.WINDOW_SIZE = 25
        print('''[Info] Initialize Radar class ''')

    def start(self, radar_cli_port, radar_data_port, radar_config_file_path, window_size=25):
        """ Radar.start """
        radar_config = []
        self.WINDOW_SIZE = window_size
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

        self.radar_parameters = self.parse_radar_config(radar_config)
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
        radar_parameters["num_doppler_bins"] = num_chirps_per_frame / \
            self.num_tx_ant
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
                    self.byte_buffer_length = self.byte_buffer_length - \
                        startIdx[0]

                # Check that there have no errors with the byte buffer length
                if self.byte_buffer_length < 0:
                    self.byte_buffer_length = 0

                # Read the total packet length
                totalPacketLen = np.matmul(
                    self.byte_buffer[12:12+4], self.word)
                # Check that all the packet has been read
                if (self.byte_buffer_length >= totalPacketLen) and (self.byte_buffer_length != 0):
                    magicOK = 1

        rangeArray = []
        dopplerArray = []
        rangeDoppler = []
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
                detectedNoise_array, \
                rangeArray, \
                dopplerArray, \
                rangeDoppler = parser_one_mmw_demo_output_packet(
                    allBinData[totalBytesParsed::1], readNumBytes-totalBytesParsed, self.radar_parameters, self.debug)

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

                detObj = {"numObj": numDetObj, "range": detectedRange_array, "doppler": detectedV_array,
                          "x": detectedX_array, "y": detectedY_array, "z": detectedZ_array,
                          "elevation": detectedElevation_array, "azimuth": detectedAzimuth_array, "snr": detectedSNR_array,
                          "rangeArray": rangeArray, "dopplerArray": dopplerArray,
                          "rangeDoppler": rangeDoppler, "doppler": detectedV_array,
                          "snr": detectedSNR_array,  "noise": detectedNoise_array
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
        azi_vals = 0
        eln_vals = 0
        num_points = 0
        snr_max = 200
        zero_pt = np.zeros((1, 9))  # for initial zero value

        # get average point per frame
        if data_ok:
            pos_pt = np.zeros((detection_obj["numObj"], 9))
            avg_pt = zero_pt

            pos_pt = np.array(list(map(tuple, np.stack([
                detection_obj["x"], detection_obj["y"], detection_obj["z"], detection_obj["doppler"],
                detection_obj["range"], detection_obj["snr"], detection_obj["azimuth"], detection_obj["elevation"]], axis=1))))

            # 取出符合條件的索引
            indices = np.where(pos_pt[:, 5] > snr_max)
            x_vals, y_vals, z_vals, doppler_vals, range_vals, snr_vals, azi_vals, eln_vals = pos_pt[indices, :9].T

            # 計算平均值
            x_value = np.mean(x_vals)
            y_value = np.mean(y_vals)
            z_value = np.mean(z_vals)
            doppler_value = np.mean(doppler_vals)
            range_value = np.mean(range_vals)
            snr_value = np.mean(snr_vals)
            azi_vals = np.mean(azi_vals)
            eln_vals = np.mean(eln_vals)
            num_points += len(indices[0])
            save_point = 0

            if num_points > 0:
                avg_pt = np.array([[x_value, y_value, z_value, doppler_value,
                                  range_value, snr_value, azi_vals, eln_vals, time.time()]])
                return avg_pt
            else:
                avg_pt = zero_pt
                return avg_pt

    def data_to_numpy(self, npy_file_dir, npy_file_name, pic_file_dir):
        filecount = len(os.listdir(npy_file_dir)) - 1
        filename = f"{npy_file_dir}/{npy_file_name}_{filecount}.npy"

        data_frame = pd.DataFrame(self.window_buffer, columns=[
                                  'x', 'y', 'z', 'doppler', 'range', 'snr', 'azimuth', 'elevation', 'time']).drop('time', axis=1)

        data_frame.replace(0, np.nan, inplace=True)

        dataframe_interpolated = data_frame.interpolate(method='linear', limit_direction='both')

        start_index = data_frame.first_valid_index()
        end_index = data_frame.last_valid_index()

        if start_index is not None:
            dataframe_interpolated.iloc[:start_index] = data_frame.iloc[:start_index]
        if end_index is not None:
            dataframe_interpolated.iloc[end_index + 1:] = data_frame.iloc[end_index + 1:]

        interpolated_npy = dataframe_interpolated.fillna(0).to_numpy()
        np.save(filename, interpolated_npy)
        print(f"Gesture data {filecount} has been saved.")

        self.plot_data(interpolated_npy, filecount, pic_file_dir)

    def plot_data(self, np_array, filecount, pic_file_dir):
        y_ranges = {'Range': (-0.2, 0.8), 'Doppler': (-2.5, 2.5), 'Azimuth': (-60, 60), 'Elevation': (-60, 60)}
        for param, y_range in y_ranges.items():
            index = {'Range': 4, 'Doppler': 3, 'Azimuth': 6, 'Elevation': 7}[param]
            self.plot_parameter_over_time(np_array, index, param, filecount, y_range, pic_file_dir)

    def plot_parameter_over_time(self, np_array, param_index, param_name, number, y_range, pic_file_dir):
        times = np.arange(np_array.shape[0])
        values = np_array[:, param_index]

        background_color = (0.8, 0.8, 0.8)
        line_color = (0.2, 0.2, 0.2)

        plt.figure(figsize=(4, 4), facecolor=background_color)
        plt.plot(times, values, linewidth=3, color=line_color)
        plt.ylim(y_range)
        plt.axis('off')
        plt.gca().set_position([0, 0, 1, 1])
        plt.gca().set_aspect('auto')

        img_filename = f'{pic_file_dir}/yuan_data_{number}_{param_name.lower()}.png'
        # plt.savefig(f'{pic_file_dir}/aimage_{param_name.lower()}.png', bbox_inches='tight', pad_inches=0, dpi=80)
        plt.savefig(img_filename, bbox_inches='tight', pad_inches=0, dpi=80)
        plt.close()
        print(f"Gesture data {number} has been saved as image: {img_filename}.")

    def data_to_csv(self):
        """Process the data points in a window and perform gesture recognition."""
        # Example: Save the window data to a file
        with open('gesture_data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # writer.writerow(window_data)
            for window in self.window_buffer:
                # print(window)
                writer.writerow(window)

    def sliding_window(self, data):
        self.window_buffer = np.row_stack((self.window_buffer, data[0]))

    def change_time_unit(self, tmp_arr):
        """ change time unit """
        stime = tmp_arr[0][6]
        new_arr = tmp_arr
        arr_len = len(tmp_arr)
        for i in range(arr_len):
            new_arr[i][6] = new_arr[i][6] - stime
        return new_arr
