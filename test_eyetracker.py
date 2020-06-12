#! /usr/bin/env python
""" A script for testing the on-screen eyetracker gaze marking python interface
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

import pyximport; pyximport.install()

from lib.py.eyetracker_gaze import EyeTrackerGaze

DURATION_S = 1

if __name__ == "__main__":
    e = EyeTrackerGaze()
    
    e.open()
    e.start()

    print(f'Marking gaze...')
    time.sleep(DURATION_S)
    # e.to_csv('test.csv', 0)
    
    e.stop()
    e.close()

