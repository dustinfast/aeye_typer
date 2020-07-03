#! /usr/bin/env python
""" A script for testing the on-screen eyetracker gaze marking python interface
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import time

import pyximport; pyximport.install()

from lib.py.eyetracker_gaze import EyeTrackerGaze

DURATION_S = 2

if __name__ == "__main__":
    e = EyeTrackerGaze(
        '/opt/app/data/aeye_typer/event_logs/raw/hud/2020-06-13_x.pkl',
        '/opt/app/data/aeye_typer/event_logs/raw/hud/2020-06-13_y.pkl')
    
    e.open()
    e.start()

    print(f'Marking gaze...')
    time.sleep(DURATION_S)
    
    e.stop()
    e.close()

