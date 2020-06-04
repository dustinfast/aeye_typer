#! /usr/bin/env python
#cython: language_level=3
""" A ctypes wrapper for the EyeTrackerGaze CPP class.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import ctypes
from subprocess import Popen, PIPE

from lib.py.app import config, info, warn, error

_conf = config()
LIB_PATH = _conf['EYETRACKER_EXTERN_LIB_PATH']
DISP_WIDTH_MM = _conf['DISP_WIDTH_MM']
DISP_HEIGHT_MM = _conf['DISP_HEIGHT_MM']
DISP_WIDTH_PX = _conf['DISP_WIDTH_PX']
DISP_HEIGHT_PX = _conf['DISP_HEIGHT_PX']
GAZE_SAMPLE_HZ = _conf['EYETRACKER_SAMPLE_HZ']
GAZE_BUFF_SZ = _conf['EYETRACKER_BUFF_SZ']
GAZE_MARK_INTERVAL = _conf['EYETRACKER_MARK_INTERVAL']
GAZE_PREP_PATH = _conf['EYETRACKER_PREP_SCRIPT_PATH']
del _conf


class EyeTrackerGaze(object):
    def __init__(self):
        # Build external .so file
        prep_proc = Popen([GAZE_PREP_PATH], stderr=PIPE)
        stderr = prep_proc.communicate()[1]
        prep_proc.wait()

        # If there were build errors, quit
        if stderr and not stderr.decode().startswith('Created symlink'):
            error(f'Eyetracker .so build failed with:\n {stderr}')
            exit()

        self._lib = self._init_lib(LIB_PATH)
        self.sample_rate = GAZE_SAMPLE_HZ
        self._obj = None  # Populated on open()

    @staticmethod
    def _init_lib(lib_path):
        """ Loads the external lib, inits callables, and returns a ctypes.cdll.
        """
        lib = ctypes.cdll.LoadLibrary(lib_path)
        
        # Constructor
        lib.eyetracker_gaze_new.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_int, 
                ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.eyetracker_gaze_new.restype = ctypes.c_void_p

        # Destructor
        lib.eyetracker_gaze_destructor.argtypes = [ctypes.c_void_p]
        lib.eyetracker_gaze_destructor.restype = ctypes.c_void_p

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

        # Gaze data sz
        lib.eyetracker_gaze_data_sz.argtypes = [ctypes.c_void_p]
        lib.eyetracker_gaze_data_sz.restype = ctypes.c_int

        return lib

    def _ensure_device_opened(self):
        if self._obj is None:
            raise EnvironmentError('An EyeTrackerGaze.open() is required.')

    def open(self):
        """ Opens the device for use.
        """
        if self._obj is not None:
            warn('Device already open.')
            return

        self._obj = self._lib.eyetracker_gaze_new(
            DISP_WIDTH_MM, DISP_HEIGHT_MM, DISP_WIDTH_PX, DISP_HEIGHT_PX,
                GAZE_MARK_INTERVAL, GAZE_BUFF_SZ)

    def start(self):
        """ Starts the asynchronous gaze tracking.
        """
        self._ensure_device_opened()
        self._lib.eyetracker_gaze_start(self._obj)

    def stop(self):
        """ Stops the asynchronous gaze tracking.
        """
        self._ensure_device_opened()
        self._lib.eyetracker_gaze_stop(self._obj)
        
    def close(self):
        """ Closes the device.
        """
        if self._obj is None:
            error('Device not open.')

        self._lib.eyetracker_gaze_destructor(self._obj)
        self._obj = None

    def to_csv(self, file_path, num_points=0):
        """ Writes up to the last n gaze data points to the given file path,
            creating it if exists else appending to it.
            If n == 0, all data points in the buffer are written.
        """
        self._ensure_device_opened()
        self._lib.eyetracker_gaze_to_csv(self._obj, 
                                        bytes(file_path, encoding="ascii"),
                                        num_points)

    def gaze_data_sz(self):
        """ Returns the number of gaze point samples in the eyetracker's buff.
        """
        self._ensure_device_opened()
        return self._lib.eyetracker_gaze_data_sz(self._obj)