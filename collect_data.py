#! /usr/bin/env python
""" A module for running the EEG and Keyboard/Mouse Event loggers.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com], 2020'

import argparse
from time import sleep

from lib.py import app
from lib.py.event_logger import (AsyncEEGEventLogger, 
                                 AsyncInputEventLogger,
                                 AsyncGazeEventLogger)


# App config constants
_conf = app.config()
WRITE_BACK = _conf['EVENTLOG_WRITEBACK_SECONDS']
WRITE_AFTER = _conf['EVENTLOG_WRITEAFTER_SECONDS']
del _conf


# Log setup
LOG_NAME = 'cfg0_log0'
LOG_NOTES = ('# Log Notes\n'
             '  \n'
             'First set of logs containing gaze_point_data.\n'
             'Git commit hash: e7785f  \n'
             '  \n'
             '## Channels\n'
             '  \n'
             '| # | 10-20 |\n'
             '|---| ----- |\n'
             '| 0 | Time  |\n'
             '| 1 | FP1   |\n'
             '| 2 | FP2   |\n'
             '| 3 | C3    |\n'
             '| 4 | C4    |\n'
             '| 5 | P7    |\n'
             '| 6 | P8    |\n'
             '| 7 | O1    |\n'
             '| 8 | O2    |\n'
             '  \n'
             'Writeback = 7s  \n'
             'Writeforward = 7s  \n'
)


if __name__ == "__main__":
    # Setup cmd line args
    parser = argparse.ArgumentParser()
    arg_flags = ('-e', '--eeg_off')
    arg_help_str = 'Run with EEG event logging turned off.'
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
    arg_flags = ('-n', '--name')
    arg_help_str = 'A descriptive/friendly name for the log.'
    parser.add_argument(*arg_flags,
                        type=str,
                        default=LOG_NAME,
                        help=arg_help_str)
    arg_flags = ('-v', '--verbose')
    arg_help_str = 'Verbose output mode.'
    parser.add_argument(*arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)                        
    args = parser.parse_args()

    # Prompt to continue
    _ = input('\nPress Enter to confirm your devices are turned on/grounded')

    # Init and start the EEG board and key/mouse event loggers
    eeg_logger = AsyncEEGEventLogger(
        args.name, LOG_NOTES, WRITE_BACK, WRITE_AFTER, args.verbose)
    gaze_logger = AsyncGazeEventLogger(
        args.name, LOG_NOTES, WRITE_BACK, WRITE_AFTER, args.verbose)

    # The eeg and gaze loggers only write to file when signaled by the input
    # logger, so we define the callbacks that do that signaling.
    eeg_callback = None if args.eeg_off else eeg_logger.event 
    gaze_callback = None if args.gaze_off else gaze_logger.event 
    
    input_logger = AsyncInputEventLogger(
        args.name, LOG_NOTES, [eeg_callback, gaze_callback], args.verbose)

    # Start the loggers
    eeg_logger.start() if not args.eeg_off else None
    gaze_logger.start() if not args.gaze_off else None
    log_proc = input_logger.start()

    # Wait for key logger to terminate via the keystroke combo SHIFT + ESC
    app.bold('\nRunning... Press SHIFT + ESC from anywhere to terminate.\n')
    log_proc.join()

    # Cleanup
    eeg_logger.stop() if not args.eeg_off else None
    gaze_logger.stop() if not args.gaze_off else None