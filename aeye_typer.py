#! /usr/bin/env python
""" The AI TypeR launcher.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import argparse
from subprocess import Popen

from lib.py.hud import HUD
from lib.py.hud_learn import HUDTrain


CMD_CALIBRATE = 'tobiiproeyetrackermanager'

if __name__ == "__main__":
    # Setup cmd line args
    # TODO: Some args are mutually exclusive
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
    arg_flags = ('-t', '--train_ml')
    arg_help_str = 'Runs training of the applications ML models.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    args = parser.parse_args()

    if args.calibrate:
        proc = Popen([CMD_CALIBRATE])
    elif args.data_collect:
        HUD(mode='collect').run()
    elif args.train_ml:
        HUDTrain().run()