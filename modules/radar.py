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
        print('''[Info] Initialize Radar class ''')
    
    def serialConfig(self, configFileName, cliPort, dataPort):
        """ Serial encoding"""
        self.CLIport = serial.Serial(cliPort, 115200)
        self.Dataport = serial.Serial(dataPort, 921600)

        # Read the configuration file and send it to the board
        config = [line.rstrip('\r\n') for line in open(configFileName)]
        for i in config:
            self.CLIport.write((i+'\n').encode())
            print(i)
            time.sleep(0.01)
    
    def parseConfigFile(self, configFileName):
        # Initialize an empty dictionary to store the configuration parameters
        configParameters = {}

        # Read the configuration file
        config = [line.rstrip('\r\n') for line in open(configFileName)]
        for i in config:
            # Split the line
            splitWords = i.split(" ")

            # Hard code the number of antennas, change if other configuration is used
            numRxAnt = 4
            numTxAnt = 1

            # Get the information about the profile configuration
            if "profileCfg" in splitWords[0]:
                startFreq = int(float(splitWords[2]))
                idleTime = int(splitWords[3])
                rampEndTime = float(splitWords[5])
                freqSlopeConst = float(splitWords[8])
                numAdcSamples = int(splitWords[10])
                numAdcSamplesRoundTo2 = 1

                while numAdcSamples > numAdcSamplesRoundTo2:
                    numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2

                digOutSampleRate = int(splitWords[11])

            # Get the information about the frame configuration
            elif "frameCfg" in splitWords[0]:
                chirpStartIdx = int(splitWords[1])
                chirpEndIdx = int(splitWords[2])
                numLoops = float(splitWords[3])
                numFrames = int(splitWords[4])
                framePeriodicity = float(splitWords[5])

        # Combine the read data to obtain the configuration parameters
        numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
        configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
        configParameters["numRangeBins"] = numAdcSamplesRoundTo2
        configParameters["rangeResolutionMeters"] = (
            3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * numAdcSamples)
        configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (
            2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
        configParameters["dopplerResolutionMps"] = 3e8 / (2 * startFreq * 1e9 * (
            idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
        configParameters["maxRange"] = (
            300 * 0.9 * digOutSampleRate)/(2 * freqSlopeConst * 1e3)
        configParameters["maxVelocity"] = 3e8 / \
            (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)

        return configParameters
    
    def readAndParseData6843(self, configParameters):
        # Initialize variables
        magicOK = 0  # Checks if magic number has been read
        dataOK = 0  # Checks if the data has been read correctly
        frameNumber = 0
        detObj = {}

        readBuffer = self.Dataport.read(self.Dataport.in_waiting)
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
        stime = tmp_arr[0][3]
        new_arr = tmp_arr
        arr_len = len(tmp_arr)

        for i in range(arr_len):
            new_arr[i][3] = new_arr[i][3] - stime

        return new_arr