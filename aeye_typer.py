#! /usr/bin/env python
""" The AI TypeR launcher.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import argparse
from subprocess import Popen

from lib.py.hud import HUD
import lib.py.hud_learn as hud_learn

import pyximport; pyximport.install()
from lib.py.eyetracker_gaze import EyeTrackerGaze

CMD_CALIBRATE = 'tobiiproeyetrackermanager'

if __name__ == "__main__":
    # Setup CLI args
    parser = argparse.ArgumentParser()
    arg_flags = ('-c', '--calibrate')
    arg_help_str = 'Runs eyetracker device calibration.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    arg_flags = ('-d', '--data_collect')
    arg_help_str = 'Runs application in training-data collection mode.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    arg_flags = ('-i', '--infer')
    arg_help_str = 'Runs application in ml-assist mode.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    arg_flags = ('-t', '--train_ml')
    arg_help_str = 'Runs training of the application\'s ML models.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    # TODO: Screen res/sz option
    args = parser.parse_args()

    # Some CLI args are mutually exclusive -- ensure they were given that way
    if sum([args.calibrate, args.data_collect, args.infer, args.train_ml]) > 1:
        raise Exception('Invalid use of mutually exclusive cmd line args.')

    # Run the application in the specified mode
    if args.calibrate:
        # Run the external calibration tool and wait for quit
        e = EyeTrackerGaze()
        proc = Popen([CMD_CALIBRATE])
        proc.wait()

        # Write the calibration to file
        e.open()
        e.write_calibration()
        e.close()

    elif args.data_collect:
        hud_learn.HUDDataGazeAccAssist().collect()
    elif args.infer:
        HUD(mode='infer').run()
    elif args.train_ml:
        hud_learn.HUDTrainGazeAccAssist().run()
    else:
        HUD(mode='basic').run()

