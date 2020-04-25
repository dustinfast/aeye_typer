#! /usr/bin/env python
""" A module for testing the application's connection to the EEG.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import time
import numpy as np
import pandas as pd

from lib.py.eeg_brainflow import EEGBrainflow


DATA_GATHER_TIME = 3  # seconds


if __name__ == "__main__":

    # Init the board
    eeg = EEGBrainflow(False)

    # Start data stream
    print(f'Gathering {DATA_GATHER_TIME} seconds worth of data w/ ' +
          f'sample rate = {eeg.sample_rate}')
    
    data = eeg.stream_wait(DATA_GATHER_TIME)

    # Write result to stdout
    if data is not None:
        print('Received data:')
        print(data)
        print(f'Shape = {data.shape}')  # shape = [channels x data_points]
    else:
        print('No data received')
