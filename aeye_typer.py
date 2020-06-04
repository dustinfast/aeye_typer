#! /usr/bin/env python
""" The AI TypeR launcher.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import pyximport; pyximport.install()

from lib.py.eyetracker_gaze import EyeTrackerGaze
from lib.py.hud import HUD


if __name__ == "__main__":
    e = EyeTrackerGaze()
    k = HUD()
    
    e.open()
    e.start()

    k.run()

    e.stop()
    e.close()
