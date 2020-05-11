#! /usr/bin/env python
""" A script for testing the on-screen eyetracker gaze marking python interface
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

from lib.py.eyetracker_gaze import EyeTrackerGaze


TEST_DURATION = 600

if __name__ == "__main__":
    e = EyeTrackerGaze()
    
    e.open()
    e.start()
    print(f'Marking gaze for {TEST_DURATION} seconds...')

    for _ in range(TEST_DURATION):
        time.sleep(1)
        # e.to_csv('test.csv', 10)

    t_start = time.time()
    e.stop()
    print(f'stopped in {1000 * (time.time() - t_start)}\n')

    t_start = time.time()
    e.close()
    print(f'closed in {1000 * (time.time() - t_start)}\n')
