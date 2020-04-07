#! /usr/bin/env python

import time
import numpy as np
import pandas as pd

from lib.py.eeg_brainflow import EEGBrainflow


DATA_GATHER_TIME = 3  # seconds


if __name__ == "__main__":

    # Init the board
    eeg = EEGBrainflow(False)

    sample_rate = eeg.sample_rate
    eeg_channels = eeg.eeg_channels
    tstamp_channel = eeg.time_channel

    # Start data stream
    print(f'Gathering {DATA_GATHER_TIME} seconds worth of data w/ ' +
          f'sample rate = {sample_rate}')
    
    data = eeg.stream_wait(DATA_GATHER_TIME)

    if data is not None:
        # Write to stdout
        print('Received data:')
        print(data)
        print(f'Shape = {data.shape}')  # shape = [channels x data_points]
