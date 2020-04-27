#! /usr/bin/env python
""" A ctypes wrapper for the EyeTrackerGaze class.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

from lib.py import app
from lib.py.eyetracker_gaze import EyeTrackerGaze


# App config constants
_conf = app.config()
LOG_ROOTDIR = _conf['EVENTLOG_ROOTDIR']
DISP_WIDTH = _conf['DISP_WIDTH']
DISP_HEIGHT = _conf['DISP_HEIGHT']
MARK_INTERVAL = _conf['EYETRACKER_MARK_INTERVAL']
GAZE_BUFF_SZ = _conf['EYETRACKER_BUFF_SZ']
del _conf

TEST_DURATION = 5

if __name__ == "__main__":
    # Compile the shared obj file from source
    # from subprocess import Popen, PIPE
    # self._bci_hub_proc = Popen([BCI_HUB_PATH])
    # time.sleep(1)

    # if self._bci_hub_proc.poll() is not None:
    #     print(f'WARN: Could not start {BCI_HUB_PATH} - ' +
    #         'It may already be running.')
    # else:
    #     print('INFO: Started OpenBCI_Hub.')


    e = EyeTrackerGaze(DISP_WIDTH, DISP_HEIGHT, MARK_INTERVAL, GAZE_BUFF_SZ)
    e.start()
    time.sleep(TEST_DURATION)
    e.stop()
