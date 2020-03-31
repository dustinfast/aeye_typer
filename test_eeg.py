#! /usr/bin/env python2

# Adapted from Emotiv Community SDK: https://github.com/Emotiv/community-sdk

import sys
import os
import platform
import time
import ctypes

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


# -------------------------------------------------------------------------
print "Connecting to device..."

if libEDK.IEE_EngineConnect("Emotiv Systems-5") != 0:
    print "Emotiv Engine start up failed."
    exit()

print("Waiting for information state update from device...")

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
                
                print('Up Time: ', systemUpTime, "\n")
                print('Wireless Strength: ', wirelessStrength, "\n")
                print('Battery: ', batteryLevel.value, "\n")
                print('\n')
                break
                             
    elif state != 0x0600:
        print "Internal error in Emotiv Engine ! "

# -------------------------------------------------------------------------
# Cleanup
libEDK.IEE_EngineDisconnect()
libEDK.IEE_EmoStateFree(eState)
libEDK.IEE_EmoEngineEventFree(eEvent)
