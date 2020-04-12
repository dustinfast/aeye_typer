#! /usr/bin/env python
""" A module for running the EEG and Keyboard/Mouse Event loggers.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com], 2020'

import argparse
from time import sleep

from lib.py import app
from lib.py.event_loggers import AsyncEEGEventLogger, AsyncInputEventLogger


# App config constants
_conf = app.config()
WRITE_BACK = _conf['EVENTLOG_EEG_WRITEBACK_SECONDS']
WRITE_AFTER = _conf['EVENTLOG_EEG_WRITEAFTER_SECONDS']
del _conf


# Log setup
LOG_NAME = 'cgf0_log_0'
LOG_NOTES = ('# Log 0\n'
             '  \n'
             'Initial Log  \n'
             'Git commit hash: 7552d7  \n'
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
)


if __name__ == "__main__":
    # Setup cmd line args
    parser = argparse.ArgumentParser()
    arg_flags = ('-e', '--eeg_off')
    arg_help_str = 'Run with0 EEG event logging turned off.'
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

    # Init and start the EEG board and key/mouse event loggers
    eeg_logger = AsyncEEGEventLogger(
        LOG_NAME, LOG_NOTES, WRITE_BACK, WRITE_AFTER, args.verbose)

    eeg_event_callback = None if args.eeg_off else eeg_logger.event 
    
    input_logger = AsyncInputEventLogger(
        LOG_NAME, LOG_NOTES, eeg_event_callback, args.verbose)

    # Start the loggers
    eeg_logger.start() if not args.eeg_off else None
    k = input_logger.start()

     # Allow time for everything to spin up
    sleep(1.5)
    print('\n*** Running... Press SHIFT + ESC from anywhere to terminate.\n')

    # Wait for key logger to terminate via the keystroke combo SHIFT + ESC
    k.join()

    # Cleanup
    eeg_logger.stop() if not args.eeg_off else None
