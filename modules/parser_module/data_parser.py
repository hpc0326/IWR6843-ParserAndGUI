import struct
import math
import binascii
import codecs
import numpy as np
# from modules.parser_module import data_parser

###global parameter area ###
PI = 3.14159265
############################



def getUint32(data):
    """!
       This function coverts 4 bytes to a 32-bit unsigned integer.

        @param data : 1-demension byte array  
        @return     : 32-bit unsigned integer
    """ 
    return (data[0] +
            data[1]*256 +
            data[2]*65536 +
            data[3]*16777216)

def getUint16(data):
    """!
       This function coverts 2 bytes to a 16-bit unsigned integer.

        @param data : 1-demension byte array
        @return     : 16-bit unsigned integer
    """ 
    return (data[0] +
            data[1]*256)

def getHex(data):
    """!
       This function coverts 4 bytes to a 32-bit unsigned integer in hex.

        @param data : 1-demension byte array
        @return     : 32-bit unsigned integer in hex
    """         
    #return (binascii.hexlify(data[::-1]))
    word = [1, 2**8, 2**16, 2**24]
    return np.matmul(data,word)


### All the parsers here are not in used. #######

def parse_type1(data, numDetobj, tlvStart, offset):
    
    """
        TLV Value Type : Detected Points
        Type: 1
        Length: 16 Bytes x Num Detected Obj
        Value: Array of detected points. Each point is represented by 16 bytes giving position and radial Doppler velocity.
    """
    
    detectedX_array = []
    detectedY_array = []
    detectedZ_array = []
    detectedV_array = []
    detectedRange_array = []
    detectedAzimuth_array = []
    detectedElevAngle_array = []
    
    
    for obj in range(numDetobj):
        # convert byte0 to byte3 to float x value
        x = struct.unpack('<f', codecs.decode(binascii.hexlify(data[tlvStart + offset:tlvStart + offset+4:1]),'hex'))[0]

        # convert byte4 to byte7 to float y value
        y = struct.unpack('<f', codecs.decode(binascii.hexlify(data[tlvStart + offset+4:tlvStart + offset+8:1]),'hex'))[0]

        # convert byte8 to byte11 to float z value
        z = struct.unpack('<f', codecs.decode(binascii.hexlify(data[tlvStart + offset+8:tlvStart + offset+12:1]),'hex'))[0]

        # convert byte12 to byte15 to float v value
        v = struct.unpack('<f', codecs.decode(binascii.hexlify(data[tlvStart + offset+12:tlvStart + offset+16:1]),'hex'))[0]

        # calculate range profile from x, y, z
        compDetectedRange = math.sqrt((x * x)+(y * y)+(z * z))

        # calculate azimuth from x, y           
        if y == 0:
            if x >= 0:
                detectedAzimuth = 90
            else:
                detectedAzimuth = -90 
        else:
            detectedAzimuth = math.atan(x/y) * 180 / PI

        # calculate elevation angle from x, y, z
        if x == 0 and y == 0:
            if z >= 0:
                detectedElevAngle = 90
            else: 
                detectedElevAngle = -90
        else:
            detectedElevAngle = math.atan(z/math.sqrt((x * x)+(y * y))) * 180 / PI
                
        detectedX_array.append(x)
        detectedY_array.append(y)
        detectedZ_array.append(z)
        detectedV_array.append(v)
        detectedRange_array.append(compDetectedRange)
        detectedAzimuth_array.append(detectedAzimuth)
        detectedElevAngle_array.append(detectedElevAngle)
                                                    
        offset = offset + 16
    # end of for obj in range(numDetObj) for 1st TLV
    
    return {"detectedX_array" : detectedX_array,
            "detectedY_array" : detectedY_array,
            "detectedZ_array" : detectedZ_array,
            "detectedV_array" : detectedV_array,
            "detectedRange_array" : detectedRange_array,
            "detectedAzimuth_array" : detectedAzimuth_array,
            "detectedElevAngle_array" : detectedElevAngle_array}

def parse_type2(data):
    
    """
        TLV Value Type : Range Profile
        Type: 2
        Length: 2 Bytes x Range FFT size
        Value: Array of profile points at 0th Doppler (stationary objects). The points represent the sum of log2 magnitudes of received antennas expressed in Q9 format.
    """
    
    
def parse_type3(data):
    
    """
        TLV Value Type : Noise Profile
        Type: 3
        Length: 2 Bytes x Range FFT size
        Value: Array of profile points at max Doppler bin. In general for stationary scene, 
        there would be no objects or clutter at maximum speed so the range profile at such speed represents the receiver noise floor.
    """
    

def parse_type4(data):
    
   """ 
        TLV Value Type : Azimuth Static Heatmap
        Type: 4
        Length: (Range FFT size) x (Number of “azimuth” virtual antennas) x (4Bytes)
        Value:  Samples to calculate static azimuth heatmap (no moving object signal). 
                This is a 2D FFT array in range direction (x[numRangeBins][numVirtualAntAzim]), 
                at doppler index 0. The antenna data are complex symbols, with imaginary first and real second in the following order:

                    Imag(ant 0, range 0), Real(ant 0, range 0),…,Imag(ant N-1, range 0),Real(ant N-1, range 0)
                    ...
                    Imag(ant 0, range R-1), Real(ant 0, range R-1),…,Imag(ant N-1, range R-1),Real(ant N-1, range R-1)

                This means the first 4 bytes of the payload is the radar cube complex value of the first range bin for the first virtual antenna(N=1). 
                The last 4 bytes is for the last range bin (R) and the last virtual antenna (N). 
                The values from the radar cube are used to construct the range-azimuth heatmap in the visualizer.
    """
    
    
def parse_type5(data):
    
    """
        TLV Value Type : Range-Doppler Heatmap
        Type: 5
        Length: (Range FFT size) x (Doppler FFT size) x (2Bytes)
        Value:  Range/Doppler detection matrix.
                X(range bin 0, Doppler bin 0),…,X(range bin 0, Doppler bin D-1),
                …
                X(range bin R-1, Doppler bin 0),…,X(range bin R-1, Doppler bin D-1)
        
    """

def parse_type6(data):
    
    """
        TLV Value Type : Statistics
        Type: 6
        Length: 24 Bytes
        Value: Stats information from data path. See the doxygen for detailed explanation of each stat.
    """

def parse_type7(data):
    
    """
        TLV Value Type : Side Info for Detected Points
        Type: 7
        Length: 4 Bytes x Num Detected Obj
        Value: The payload consists of 4 bytes for EACH point in the point cloud. The values for snr and noise are measured in multiples of 0.1dB.
    """
    
    detectedSNR_array = []
    detectedNoise_array = []
    

def parse_type8(data):
    
    """
        TLV Value Type : Azimuth/Elevation Static Heatmap
        Type: 8
        Length: (Range FFT size) x (Number of all virtual antennas) x (4Bytes)
        Value:  Samples to calculate static azimuth or elevation heatmap (no moving object signal). 
                This is a 2D FFT array in range direction (x[numRangeBins][numVirtualAntAzim]), at doppler index 0. 
                The antenna data are complex symbols, with imaginary first and real second in the following order:
                
                    Imag(ant 0, range 0), Real(ant 0, range 0),…,Imag(ant N-1, range 0),Real(ant N-1, range 0)
                    …
                    Imag(ant 0, range R-1), Real(ant 0, range R-1),…,Imag(ant N-1, range R-1),Real(ant N-1, range R-1)
                    
        ###The demo will only output either the Azimuth Static Heatmap or the Azimuth/Elevation Static Heatmap###
    """


def parse_type9(data):
    
    """
        TLV Value Type : Temperature Statistics
        Type: 9
        Length: 28 Bytes
        Value: Temperature report - snapshot taken just before shipping data over UART
    """