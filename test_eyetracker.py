#! /usr/bin/env python
""" A script for testing the on-screen eyetracker gaze marking python interface
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

import pyximport; pyximport.install()
from lib.py.eyetracker_gaze import EyeTrackerGaze
from lib.py.hud import HUD


if __name__ == "__main__":
    e = EyeTrackerGaze()
    k = HUD()
    
    e.open()
    e.start()
    print(f'Marking gaze...')
    k.mainloop()
    # e.to_csv('test.csv', 0)

    e.stop()
    e.close()


# # TODO: From conf
# KEYB_DISP_WIDTH = 480
# KEYB_DISP_HEIGHT = 320
