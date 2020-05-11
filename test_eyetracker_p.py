#! /usr/bin/env python
""" A script for testing the on-screen eyetracker gaze marking python interface
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

from lib.py.eyetracker_gaze import EyeTrackerGaze


TEST_DURATION = 1200

if __name__ == "__main__":
    e = EyeTrackerGaze()
    
    print(f'Marking gaze for {TEST_DURATION} seconds...')
    e.start()
    time.sleep(TEST_DURATION)
    # e.to_csv('test.csv', 4)
    e.stop()
