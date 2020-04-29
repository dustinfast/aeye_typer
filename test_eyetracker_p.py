#! /usr/bin/env python
""" A ctypes wrapper for the EyeTrackerGaze class.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time
from subprocess import Popen, PIPE

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

TEST_DURATION = 1

if __name__ == "__main__":
    print('Prepping eyetracker...')
    prep_proc = Popen([GAZE_PREP_PATH], stderr=PIPE)
    stderr = prep_proc.communicate()[1]
    prep_proc.wait()

    if stderr:
        print('Prep failed with:', stderr, 'Quitting.', sep='\n')
        exit()

    print(f'Marking gaze for {TEST_DURATION} seconds...')
    e = EyeTrackerGaze(DISP_WIDTH, DISP_HEIGHT, MARK_INTERVAL, GAZE_BUFF_SZ)
    e.start()
    time.sleep(TEST_DURATION)
    e.to_csv('test.csv', 4)
    e.stop()
