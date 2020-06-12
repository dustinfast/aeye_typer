#cython: language_level=3
""" A ctypes wrapper for the EyeTrackerGaze CPP module.
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
GAZE_SMOOTH_OVER = _conf['EYETRACKER_SMOOTH_OVER']
del _conf


class gaze_point(ctypes.Structure):
    """ An abstraction of a gaze point, including the number of samples gaze
        samples it was smoothed over.
    """
    _fields_ = [
        ('n_samples', ctypes.c_int), 
        ('x', ctypes.c_int), 
        ('y', ctypes.c_int)]


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
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
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

        # GazePoint
        lib.eyetracker_gaze_point.argtypes = [ctypes.c_void_p]
        lib.eyetracker_gaze_point.restype = ctypes.c_void_p

        # GazePoint
        lib.eyetracker_gaze_point_free.argtypes = [ctypes.c_void_p]
        lib.eyetracker_gaze_point_free.restype = ctypes.c_void_p

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
                GAZE_MARK_INTERVAL, GAZE_BUFF_SZ, GAZE_SMOOTH_OVER)

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

    def gaze_coords(self):
        """ Returns the current gaze point in display coords.
        """
        self._ensure_device_opened()
        
        # Instantiate a gaze_point ptr from the c obj's address
        ptr = self._lib.eyetracker_gaze_point(self._obj)
        gp = gaze_point.from_address(ptr)

        # Denote the gaze_point contexts
        n = gp.n_samples
        x = gp.x
        y = gp.y

        # Free the ptr mem on the c side
        self._lib.eyetracker_gaze_point_free(ptr)

        if n <= 0:
            warn('Gaze point received from zero samples')
        
        return x, y
