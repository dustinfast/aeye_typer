#! /usr/bin/env python

import time

import numpy as np
import pandas as pd

from pynput.mouse import Button
from pynput.keyboard import Key
from pynput import mouse, keyboard

from lib.py import app
from lib.py.event_loggers import AsyncEEGEventLogger


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
    # Init the EEG board event logger
    eeg_logger = AsyncEEGEventLogger(
        LOG_NAME, LOG_NOTES, WRITE_BACK, WRITE_AFTER)

    # Start data stream watch
    eeg_logger.start()

    def on_click(x, y, button, pressed):
        if pressed:
            print(f'Mouse down at ({x}, {y}) with {button}')
        else:
            print(f'Mouse up at ({x}, {y}) with {button}')
        eeg_logger.event()
        
    
    def on_scroll(x, y, dx, dy):
        print(f'Mouse scrolled at ({x}, {y})({dx}, {dy})')
        eeg_logger.event()


    def on_press(key):
        try:
            print(f'Key {key.char} pressed at {time.time()}')
        except AttributeError:
            print(f'Special key {key} pressed at {time.time()}')
        eeg_logger.event()

    def on_release(key):
        print('{key} released')
        if key == keyboard.Key.esc:
            return False  # Stop listener
        eeg_logger.event()

    
    m = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
    m.start()
    with keyboard.Listener(on_press=on_press,on_release=on_release) as k:
        k.join()

    eeg_logger.stop()
    