#! /usr/bin/env python
""" A ctypes wrapper for the EyeTrackerGaze CPP class.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import ctypes

from lib.py import app


# Get external .so lib path from app config
_conf = app.config()
LIB_PATH = _conf['EYETRACKER_EXTERN_LIB_PATH']
del _conf


class EyeTrackerGaze(object):
    def __init__(self, disp_width, disp_height, mark_freq, buff_sz):
        self.lib = self._init_lib(LIB_PATH)

        self.obj = self.lib.eyetracker_gaze_new(
            disp_width, disp_height, mark_freq, buff_sz)

    @staticmethod
    def _init_lib(lib_path):
        """ Loads the external lib, inits callables, and returns a ctypes.cdll.
        """
        lib = ctypes.cdll.LoadLibrary(lib_path)
        
        # Constructor
        lib.eyetracker_gaze_new.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.eyetracker_gaze_new.restype = ctypes.c_void_p

        # Data to csv
        lib.eyetracker_gaze_to_csv.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        lib.eyetracker_gaze_to_csv.restype = ctypes.c_int

        # Start
        lib.eyetracker_gaze_start.argtypes = [ctypes.c_void_p]
        lib.eyetracker_gaze_start.restype = ctypes.c_void_p

        # Stop
        lib.eyetracker_gaze_stop.argtypes = [ctypes.c_void_p]
        lib.eyetracker_gaze_stop.restype = ctypes.c_void_p

        return lib

    def start(self):
        """ Starts the gaze tracker asynchronously.
        """
        self.lib.eyetracker_gaze_start(self.obj)

    def stop(self):
        """ Stops the asynchronous gaze tracker.
        """
        self.lib.eyetracker_gaze_stop(self.obj)

    def to_csv(self, file_path, num_points=0):
        """ Writes up to the last n gaze data points to the given file path,
            creating it if exists else appending to it.
            If n == 0, all data points in the buffer are written.
        """
        self.lib.eyetracker_gaze_to_csv(self.obj, 
                                        bytes(file_path, encoding="ascii"),
                                        num_points)