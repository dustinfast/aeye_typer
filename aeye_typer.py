#! /usr/bin/env python
""" The AI TypeR launcher.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import argparse
from subprocess import Popen

from lib.py.eyetracker_gaze import EyeTrackerGaze
from lib.py.hud import HUD

CMD_CALIBRATE = 'tobiiproeyetrackermanager'

if __name__ == "__main__":
    # Setup cmd line args
    parser = argparse.ArgumentParser()
    arg_flags = ('-c', '--calibrate')
    arg_help_str = 'Runs eyetracker device calibration.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    arg_flags = ('-g', '--gaze_off')
    arg_help_str = 'Run with gaze event logging turned off.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    args = parser.parse_args()

    if args.calibrate:
        proc = Popen([CMD_CALIBRATE])
        exit()

    if not args.gaze_off:
        e = EyeTrackerGaze()
        e.open()
        e.start()

    k = HUD()
    k.start()

    if not args.gaze_off:
        e.stop()
        e.close()

