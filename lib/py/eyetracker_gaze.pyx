#cython: language_level=3
""" A ctypes wrapper for the EyeTrackerGaze CPP module.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import ctypes
from pathlib import Path
from subprocess import Popen, PIPE

from lib.py.app import config, info, warn, error

_conf = config()
LIB_PATH = _conf['EYETRACKER_EXTERN_LIB_PATH']
DISP_WIDTH_MM = _conf['DISP_WIDTH_MM']
DISP_HEIGHT_MM = _conf['DISP_HEIGHT_MM']
DISP_WIDTH_PX = _conf['DISP_WIDTH_PX']
DISP_HEIGHT_PX = _conf['DISP_HEIGHT_PX']
GAZE_BUFF_SZ = _conf['EYETRACKER_BUFF_SZ']
GAZE_MARK_INTERVAL = _conf['EYETRACKER_MARK_INTERVAL']
GAZE_PREP_PATH = _conf['EYETRACKER_PREP_SCRIPT_PATH']
GAZE_SMOOTH_OVER = _conf['EYETRACKER_SMOOTH_OVER']
del _conf

GAZE_CALIB_PATH = '/opt/app/data/eyetracker.calib'


class gaze_point(ctypes.Structure):
    """ An abstraction of a gaze point, including the number of samples gaze
        samples it was smoothed over.
    """
    _fields_ = [
        ('n_samples', ctypes.c_int), 
        ('x', ctypes.c_int), 
        ('y', ctypes.c_int)]


class EyeTrackerGaze(object):
    def __init__(self, ml_x_path=None, ml_y_path=None):
        # Build external .so file
        prep_proc = Popen([GAZE_PREP_PATH], stderr=PIPE)
        stderr = prep_proc.communicate()[1]
        prep_proc.wait()

        # If there were build errors, quit
        if stderr and not stderr.decode().startswith('Created symlink'):
            error(f'Eyetracker .so build failed with:\n {stderr}')
            exit()

        self._lib = self._init_lib(LIB_PATH)
        self._obj = None  # Populated on open()
        self._ml_x_path = ml_x_path
        self._ml_y_path = ml_y_path

    @staticmethod
    def _init_lib(lib_path):
        """ Loads the external lib, inits callables, and returns a ctypes.cdll.
        """
        lib = ctypes.cdll.LoadLibrary(lib_path)
        
        # Constructor
        lib.eye_gaze_new.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_int, 
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                    ctypes.c_char_p, ctypes.c_char_p]
        lib.eye_gaze_new.restype = ctypes.c_void_p

        # Destructor
        lib.eye_gaze_destructor.argtypes = [ctypes.c_void_p]
        lib.eye_gaze_destructor.restype = ctypes.c_void_p

        # Data to csv
        lib.eye_gaze_data_tocsv.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
        lib.eye_gaze_data_tocsv.restype = ctypes.c_int

        # Start
        lib.eye_gaze_start.argtypes = [ctypes.c_void_p]
        lib.eye_gaze_start.restype = ctypes.c_void_p

        # Stop
        lib.eye_gaze_stop.argtypes = [ctypes.c_void_p]
        lib.eye_gaze_stop.restype = ctypes.c_void_p

        # Gaze data sz
        lib.eye_gaze_data_sz.argtypes = [ctypes.c_void_p]
        lib.eye_gaze_data_sz.restype = ctypes.c_int

        # User position guide, x
        lib.eye_user_pos_guide_x.argtypes = [ctypes.c_void_p]
        lib.eye_user_pos_guide_x.restype = ctypes.c_float

        # User position guide, y
        lib.eye_user_pos_guide_y.argtypes = [ctypes.c_void_p]
        lib.eye_user_pos_guide_y.restype = ctypes.c_float

        # User position guide, z
        lib.eye_user_pos_guide_z.argtypes = [ctypes.c_void_p]
        lib.eye_user_pos_guide_z.restype = ctypes.c_float

        # Set cursor capture
        lib.eye_cursor_cap.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.eye_cursor_cap.restype = ctypes.c_void_p

        # Device calibration writer
        lib.eye_write_calibration.argtypes = [ctypes.c_void_p]
        lib.eye_write_calibration.restype = ctypes.c_void_p

        # GazePoint
        lib.eye_gaze_point.argtypes = [ctypes.c_void_p]
        lib.eye_gaze_point.restype = ctypes.c_void_p

        # GazePoint mem free
        lib.eye_gaze_point_free.argtypes = [ctypes.c_void_p]
        lib.eye_gaze_point_free.restype = ctypes.c_void_p

        return lib

    def _ensure_device_opened(self):
        if self._obj is None:
            raise EnvironmentError('An EyeTrackerGaze.open() is required.')

    def open(self):
        """ Opens the device for use.
        """
        if self._obj is not None:
            error('Eyetracker.open attempted but device already open.')
            return

        try:
            ml_x_path = bytes(self._ml_x_path, encoding="ascii")
        except TypeError:
            ml_x_path = None

        try:
            ml_y_path = bytes(self._ml_y_path, encoding="ascii")
        except TypeError:
            ml_y_path = None


        self._obj = self._lib.eye_gaze_new(
            DISP_WIDTH_MM, DISP_HEIGHT_MM, DISP_WIDTH_PX, DISP_HEIGHT_PX,
                GAZE_MARK_INTERVAL, GAZE_BUFF_SZ, GAZE_SMOOTH_OVER,
                    ml_x_path, ml_y_path)

    def close(self):
        """ Closes the device.
        """
        if self._obj is None:
            warn('Eyetracker.close attempted but device not open.')

        self._lib.eye_gaze_destructor(self._obj)
        self._obj = None

    def start(self):
        """ Starts asynchronously gaze tracking.
        """
        self._ensure_device_opened()
        self._lib.eye_gaze_start(self._obj)

    def stop(self):
        """ Stops asynchronously gaze tracking.
        """
        self._ensure_device_opened()
        self._lib.eye_gaze_stop(self._obj)
        
    def to_csv(self, file_path, num_points=0, label=''):
        """ Writes up to the last n gaze data points to the given file path,
            creating it if exists else appending to it.
            If n == 0, all data points in the buffer are written.
            ASSUMES: After first call to this function, subsequent calls
            are for the same file_path (for perf reasons)
        """
        # Decode and cache the file_path.
        try:
            csv_path = self._csv_path
        except AttributeError:
            self._csv_path = bytes(file_path, encoding="ascii")
            csv_path = self._csv_path

        self._ensure_device_opened()
        self._lib.eye_gaze_data_tocsv(self._obj, 
                                      csv_path,
                                      num_points,
                                      bytes(label, encoding="ascii"))

    def gaze_data_sz(self):
        """ Returns the number of gaze point samples in the eyetracker's buff.
        """
        self._ensure_device_opened()
        return self._lib.eye_gaze_data_sz(self._obj)

    def user_pos_guide(self):
        """ Returns a tuple representing the user position guide, as (x, y, z).
        """
        self._ensure_device_opened()
        return (self._lib.eye_user_pos_guide_x(self._obj),
                self._lib.eye_user_pos_guide_y(self._obj),
                self._lib.eye_user_pos_guide_z(self._obj))

    def set_cursor_cap(self, enabled=False):
        """ Enables disables cursor capture for gaze-marking purposes.
        """
        self._ensure_device_opened()
        self._lib.eye_cursor_cap(self._obj, enabled)

    def write_calibration(self):
        """ Writes the eyetracker device's calibration data to file.
        """
        self._ensure_device_opened()

        # If exists, prompt for overwrite
        if Path(GAZE_CALIB_PATH).exists():
            warn('Calibration file exists! Overwrite it', end=' ')
            if input('[y/N]? ') != 'y':
                info('Calibration aborted by user.')
                return

        # If not exists OR if overwrite confirmed, write to file
        self._lib.eye_write_calibration(self._obj)
        info('Calibration complete.')

    def gaze_coords(self):
        """ Returns the current gaze point in display coords.
        """
        self._ensure_device_opened()
        
        # Instantiate a gaze_point ptr from the c obj's address
        ptr = self._lib.eye_gaze_point(self._obj)
        gp = gaze_point.from_address(ptr)

        # Denote the gaze_point contexts
        n = gp.n_samples
        x = gp.x
        y = gp.y

        # Free the ptr mem on the c side
        self._lib.eye_gaze_point_free(ptr)

        if n <= 0:
            warn('Gaze point received from zero samples')
        
        return x, y
