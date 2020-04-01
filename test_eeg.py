#! /usr/bin/env python2

# Adapted from Emotiv Community SDK: https://github.com/Emotiv/community-sdk

import sys
import os
import platform
import time
import ctypes
from time import sleep

import atexit
from select import select
    
from ctypes import *
from fileinput import close


try:
    libEDK = CDLL('./bin/libedk.so')
except Exception as e:
    print 'Error: cannot load EDK lib:', e
    exit()


# Lib init
IEE_EmoEngineEventCreate = libEDK.IEE_EmoEngineEventCreate
IEE_EmoEngineEventCreate.restype = c_void_p
eEvent = IEE_EmoEngineEventCreate()

IS_GetTimeFromStart = libEDK.IS_GetTimeFromStart
IS_GetTimeFromStart.argtypes = [ctypes.c_void_p]
IS_GetTimeFromStart.restype = c_float

IS_GetWirelessSignalStatus = libEDK.IS_GetWirelessSignalStatus
IS_GetWirelessSignalStatus.restype = c_int
IS_GetWirelessSignalStatus.argtypes = [c_void_p]

IEE_EmoEngineEventGetEmoState = libEDK.IEE_EmoEngineEventGetEmoState
IEE_EmoEngineEventGetEmoState.argtypes = [c_void_p, c_void_p]
IEE_EmoEngineEventGetEmoState.restype = c_int

IEE_EmoStateCreate = libEDK.IEE_EmoStateCreate
IEE_EmoStateCreate.restype = c_void_p
eState = IEE_EmoStateCreate()

IEE_MotionDataCreate = libEDK.IEE_MotionDataCreate
IEE_MotionDataCreate.restype = c_void_p
hMotionData = IEE_MotionDataCreate()

userID = c_uint(0)
user = pointer(userID)
ready = 0
state = c_int(0)
systemUpTime = c_float(0.0)

batteryLevel = c_long(0)
batteryLevelP = pointer(batteryLevel)
maxBatteryLevel = c_int(0)
maxBatteryLevelP = pointer(maxBatteryLevel)

systemUpTime = c_float(0.0)
wirelessStrength = c_int(0)

datarate = c_uint(0)
secs = c_float(1)
motionChannelList = [i for i in range(11)]

# -------------------------------------------------------------------------
print "Connecting to device..."

if libEDK.IEE_EngineConnect("Emotiv Systems-5") != 0:
    print "Emotiv Engine start up failed."
    exit()

print "Buffer size in secs: %f \n" % secs.value
print("Waiting for information state update from device...")

libEDK.IEE_MotionDataSetBufferSizeInSec(secs)

while True:    
    state = libEDK.IEE_EngineGetNextEvent(eEvent)
    
    if state == 0:
        eventType = libEDK.IEE_EmoEngineEventGetType(eEvent)
        libEDK.IEE_EmoEngineEventGetUserId(eEvent, user)
            
        if eventType == 64:  # libEDK.IEE_Event_enum.IEE_EmoStateUpdated
                        
            libEDK.IEE_EmoEngineEventGetEmoState(eEvent, eState)
            
            systemUpTime = IS_GetTimeFromStart(eState)            
            wirelessStrength = libEDK.IS_GetWirelessSignalStatus(eState)
            
            if wirelessStrength > 0:
                print (systemUpTime)
                                
                libEDK.IS_GetBatteryChargeLevel(eState, batteryLevelP, maxBatteryLevelP)
                
                print('Up Time: ' + str(systemUpTime) + "\n")
                print('Wireless Strength: ' + str(wirelessStrength) + "\n")
                print('Battery: ', batteryLevel.value, "\n")
                print('\n')

                # Print the next 10 gyro events
                print("COUNTER, GYROX, GYROY, GYROZ, ACCX, ACCY, ACCZ, MAGX, MAGY, MAGZ, TIMESTAMP")
                
                while True:
                    state = libEDK.IEE_EngineGetNextEvent(eEvent)
    
                    if state == 0:
                        eventType = libEDK.IEE_EmoEngineEventGetType(eEvent)
                        libEDK.IEE_EmoEngineEventGetUserId(eEvent, user)

                        libEDK.IEE_MotionDataUpdateHandle(userID, hMotionData)
                        nSamplesTaken = c_uint(0)
                        nSamplesTakenP = pointer(nSamplesTaken)
                        
                        libEDK.IEE_MotionDataGetNumberOfSample(hMotionData, nSamplesTakenP)
                        
                        if nSamplesTaken.value > 0:
                            i += 1
                            dataType = c_double * nSamplesTaken.value
                            data = dataType()

                            for sampleIdx in range(nSamplesTaken.value):
                                sample = []
                                for i in motionChannelList:
                                    libEDK.IEE_MotionDataGet(hMotionData, i, data, nSamplesTaken.value)
                                    sample.append(data[sampleIdx])
                                print('\t'.join([str(s) for s in sample]))

    elif state != 0x0600:
        print "Internal error in Emotiv Engine ! "

# -------------------------------------------------------------------------
# Cleanup
libEDK.IEE_EngineDisconnect()
libEDK.IEE_EmoStateFree(eState)
libEDK.IEE_EmoEngineEventFree(eEvent)
