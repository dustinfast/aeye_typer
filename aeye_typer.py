#! /usr/bin/env python
""" The AI TypeR launcher.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import argparse
from subprocess import Popen

from lib.py.hud import HUD

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
    arg_flags = ('-m', '--mode')
    arg_help_str = 'HUD mode... Either collect, train, or infer (default).'
    parser.add_argument(*arg_flags,
                        type=str,
                        default='infer',
                        help=arg_help_str)

    args = parser.parse_args()

    if args.calibrate:
        proc = Popen([CMD_CALIBRATE])
    else:
        HUD(mode=args.mode).start()