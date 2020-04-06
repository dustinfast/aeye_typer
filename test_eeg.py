#! /usr/bin/env python

import time
import numpy as np
import pandas as pd

from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations


CYTON_BOARD_ID = 0
CYTON_SERIAL_PORT = '/dev/ttyUSB0'
DATA_GATHER_TIME = 3  # seconds


if __name__ == "__main__":
    # Init the board
    params = BrainFlowInputParams()
    params.serial_port = CYTON_SERIAL_PORT
    BoardShim.disable_board_logger()
    board = BoardShim(CYTON_BOARD_ID, params)
    board.prepare_session()

    sample_rate = BoardShim.get_sampling_rate(CYTON_BOARD_ID)
    eeg_channels = BoardShim.get_eeg_channels(CYTON_BOARD_ID)
    tstamp_channel = BoardShim.get_timestamp_channel(CYTON_BOARD_ID)

    # Start data stream
    print(f'Gathering {DATA_GATHER_TIME} seconds worth of data w/ ')
    print(f'sample rate = {BoardShim.get_sampling_rate(CYTON_BOARD_ID)}')
    board.start_stream()  # Default ring buffer sz = 45000
    time.sleep(DATA_GATHER_TIME)

    # Collect data from stream and close it
    data = board.get_board_data()
    board.stop_stream()
    board.release_session()

    # Strip data down to timestamp and eeg channels only
    print(f'Shape = {data.shape}') 
    data = data[[tstamp_channel] + eeg_channels, :]

    # Write to stdout
    print('Received data:')
    print(data)
    print(f'Shape = {data.shape}')  # shape = [num_channels x num_data_points]
