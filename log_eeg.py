#! /usr/bin/env python

import time

import numpy as np
import pandas as pd

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
    # Init and start the EEG board and key/mouse event loggers
    eeg_logger = AsyncEEGEventLogger(
        LOG_NAME, LOG_NOTES, WRITE_BACK, WRITE_AFTER)

    input_logger = AsyncInputEventLogger(LOG_NAME, LOG_NOTES)

    # Start the loggers
    # eeg_logger.start()
    k = input_logger.start()

    # Wait for input logger to terminate via keystroke combo SHIFT + ESC
    k.join()

    # Cleanup
    # eeg_logger.stop()


    