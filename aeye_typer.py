#! /usr/bin/env python
""" The AI TypeR launcher.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import argparse
import pyximport; pyximport.install()

from lib.py.eyetracker_gaze import EyeTrackerGaze
from lib.py.hud import HUD


if __name__ == "__main__":
    # Setup cmd line args
    parser = argparse.ArgumentParser()
    arg_flags = ('-g', '--gaze_off')
    arg_help_str = 'Run with gaze event logging turned off.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    args = parser.parse_args()

    if not args.gaze_off:
        e = EyeTrackerGaze()
        e.open()
        e.start()

    k = HUD()
    k.start()

    if not args.gaze_off:
        e.stop()
        e.close()

