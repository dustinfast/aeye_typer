""" A module for interating with the application's OpenBCI Cyton board 
    via the Brainflow API.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import time

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from brainflow.board_shim import BrainFlowError, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations

from lib.py import app


_config = app.config()
EEG_BOARD_ID = _config['DEVICE_ID_EEG_BOARD']
EEG_BOARD_SERIAL_PORT = _config['DEVICE_ID_EEG']


class EEGBrainflow():
    def __init__(self, logger=False):
        """ An abstraction of the EEG board and its brainflow interface.
        """
        self.board = self._init_board(logger)

    def _init_board(self, logger):
        """Inits the connection to the EEG board.
        """
        # Enable or disable board's logger output
        if (logger):
            BoardShim.enable_dev_board_logger()
        else:
            BoardShim.disable_board_logger()

        params = BrainFlowInputParams()
        params.serial_port = EEG_BOARD_SERIAL_PORT
        board = BoardShim(EEG_BOARD_ID, params)
        return board
        
    @property
    def sample_rate(self):
        return BoardShim.get_sampling_rate(EEG_BOARD_ID)

    @property
    def eeg_channels(self):
        return BoardShim.get_eeg_channels(EEG_BOARD_ID)

    @property
    def timestamp_channel(self):
        return BoardShim.get_timestamp_channel(EEG_BOARD_ID)

    def stream(self, t):
        # TODO:
        try:
            self.board.prepare_session()
        except BrainFlowError:
            print('Failed to connect to board. Is dongle plugged in?')
            return
        
        self.board.start_stream()  # Default ring buffer sz = 45000
        time.sleep(t)

        # # Collect data from stream and close it
        data = self.board.get_board_data()
        self.board.stop_stream()
        self.board.release_session()

        return data
