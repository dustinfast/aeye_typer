""" A module for interacting with the application's EEG board via the
    Brainflow API.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import time

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from brainflow.board_shim import BrainFlowError, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations

from lib.py import app


_conf = app.config()
EEG_BOARD_ID = _conf['DEVICE_ID_EEG_BOARD']
EEG_BOARD_SERIAL_PORT = _conf['DEVICE_ID_EEG']
del _conf


class EEGBrainflow():
    def __init__(self, logger=False):
        """ An abstraction of the EEG board and its brainflow interface.
        """
        self.board = self._init_board(logger)  # A brainflow.BoardShim
        self.sample_rate = BoardShim.get_sampling_rate(EEG_BOARD_ID)     # int

        # Channel lists
        self.eeg_channels = BoardShim.get_eeg_channels(EEG_BOARD_ID)
        self.time_channel = BoardShim.get_timestamp_channel(EEG_BOARD_ID)
        self._channel_mask = [self.time_channel] + self.eeg_channels

    @staticmethod
    def _init_board(logger) -> BoardShim:
        """ Returns a populated BoardShim obj instantance.
        """
        # Enable or disable board's logger output
        BoardShim.enable_dev_board_logger() if logger else \
            BoardShim.disable_board_logger()

        # Init the BoardShim obj
        params = BrainFlowInputParams()
        params.serial_port = EEG_BOARD_SERIAL_PORT
        board = BoardShim(EEG_BOARD_ID, params)
        
        return board

    def _prepare_session(self) -> bool:
        """ Prepares the boardshim session and returns True on success, else
            return False.
        """
        try:
            self.board.prepare_session()
        except BrainFlowError:
            print('Failed to connect to board. Is dongle plugged in?')
            return False
        else:
            return True

    def _do_channel_mask(self, data):
        """ Returns a view of the given board data with only the timestamp
            and eeg data channels.
        """
        try:
            return data[self._channel_mask, :]
        except IndexError:
            return data  # data is likely []

    def stream_wait(self, seconds, sz_buff=45000) -> np.ndarray:
        """ Blocks for the specified number of seconds before returning any
            eeg data collected over that time.
        """
        if self._prepare_session():
            self.board.start_stream(sz_buff)
            time.sleep(seconds)

            data = self.board.get_board_data()

            self.board.stop_stream()
            self.board.release_session()

            return self._do_channel_mask(data)
