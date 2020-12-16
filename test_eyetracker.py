#! /usr/bin/env python
""" A script for testing the on-screen eyetracker gaze marking python interface
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

import pyximport; pyximport.install()

from lib.py.eyetracker_gaze import EyeTrackerGaze

DURATION_S = 3


if __name__ == "__main__":
    e = EyeTrackerGaze()
    
    e.open()
    e.start()

    print(f'Marking gaze for {DURATION_S} seconds...')
    time.sleep(DURATION_S)
    
    e.stop()
    e.close()
