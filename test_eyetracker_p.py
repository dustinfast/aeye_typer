#! /usr/bin/env python
""" A ctypes wrapper for the EyeTrackerGaze class.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time
from subprocess import Popen

from lib.py import app
from lib.py.eyetracker_gaze import EyeTrackerGaze


# App config constants
_conf = app.config()
DISP_WIDTH = _conf['DISP_WIDTH']
DISP_HEIGHT = _conf['DISP_HEIGHT']
MARK_INTERVAL = _conf['EYETRACKER_MARK_INTERVAL']
GAZE_BUFF_SZ = _conf['EYETRACKER_BUFF_SZ']
GAZE_PREP_PATH = _conf['EYETRACKER_PREP_SCRIPT_PATH']
del _conf

TEST_DURATION = 5

if __name__ == "__main__":
    print('Prepping eyetracker...')
    prep_proc = Popen([GAZE_PREP_PATH])
    prep_proc.wait()

    print(f'Marking gaze for {TEST_DURATION} seconds...')
    e = EyeTrackerGaze(DISP_WIDTH, DISP_HEIGHT, MARK_INTERVAL, GAZE_BUFF_SZ)
    e.start()
    time.sleep(TEST_DURATION)
    e.stop()
