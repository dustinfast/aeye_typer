#! /usr/bin/env python

import argparse
from time import sleep

from pynput.mouse import Button
from pynput.keyboard import Key
from pynput import mouse, keyboard

from lib.py import app
from lib.py.event_loggers import AsyncEEGEventLogger, AsyncInputEventLogger


# App config constants
_conf = app.config()
WRITE_BACK = _conf['EVENTLOG_EEG_WRITEBACK_SECONDS']
WRITE_AFTER = _conf['EVENTLOG_EEG_WRITEAFTER_SECONDS']
del _conf


# Log setup
LOG_NAME = 'testlog_0'
LOG_NOTES = ('# Test Log 0  \n'
             'Initial Tests  \n'
             '## Channels  \n'
             '| # | Color  | 10-20 |\n'
             '|---| ------ | ----- |\n'
             '| 0 | NA     | Time  |\n'
             '| 1 | Purple | FP1   |\n'
             '| 2 | Gray   | FP2   |\n'
             '| 3 | Green  | C3    |\n'
             '| 4 | Blue   | C4    |\n'
             '| 5 | Orange | P7    |\n'
             '| 6 | Yellow | P8    |\n'
             '| 7 | Red    | O1    |\n'
             '| 8 | Brown  | O2    |\n'
)


if __name__ == "__main__":
    # Setup cmd line args
    parser = argparse.ArgumentParser()
    arg_flags = ('-n', '--name')
    arg_help_str = 'A descriptive/friendly name for the log.'
    parser.add_argument(*arg_flags,
                        type=str,
                        default=LOG_NAME,
                        help=arg_help_str)
    arg_flags = '--no_eeg_log'
    arg_help_str = 'Disables EEG event logging.'
    parser.add_argument(arg_flags,
                        action='store_true',
                        default=False,
                        help=arg_help_str)
    args = parser.parse_args()

    # Init and start the EEG board and key/mouse event loggers
    eeg_logger = AsyncEEGEventLogger(
        LOG_NAME, LOG_NOTES, WRITE_BACK, WRITE_AFTER)

    eeg_event_callback = None if args.no_eeg_log else eeg_logger.event 
    
    input_logger = AsyncInputEventLogger(
        LOG_NAME, LOG_NOTES, eeg_event_callback)

    # Start the loggers
    eeg_logger.start() if not args.no_eeg_log else None
    k = input_logger.start()

    # Wait for input logger to terminate via keystroke combo SHIFT + ESC
    sleep(2) # Allow everything to spin up
    print('\n*** Running... Press SHIFT + ESC from anywhere to terminate.\n')
    k.join()

    # Cleanup
    eeg_logger.stop() if not args.no_eeg_log else None


    