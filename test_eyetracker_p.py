#! /usr/bin/env python
""" A script for testing the on-screen eyetracker gaze marking python interface
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

import pyximport; pyximport.install()
from lib.py.eyetracker_gaze import EyeTrackerGaze
from lib.py.onscreen_keyboard import OnscreenKeyboard


TEST_DURATION = 10

if __name__ == "__main__":
    e = EyeTrackerGaze()
    k = OnscreenKeyboard()
    
    e.open()
    e.start()
    print(f'Marking gaze for {TEST_DURATION} seconds...')
    k.mainloop()
    print('sleeping')
    time.sleep(TEST_DURATION)
    print('done sleeping')
    # e.to_csv('test.csv', 0)

    e.stop()
    e.close()
