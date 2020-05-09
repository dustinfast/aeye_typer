""" A module for interacting with the application's EEG board via the
    Brainflow API.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import os
import time
import queue
from subprocess import Popen, PIPE
import multiprocessing as mp
from datetime import datetime
from pathlib import Path

import numpy as np
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.board_shim import BrainFlowError

from lib.py.app import config, info, warn, error

# App config constants
_conf = config()
BCI_HUB_PATH = _conf['EEG_BCI_HUB_PATH']
EEG_SZ_DATA_BUFF = _conf['EEG_SZ_DATA_BUFF']
EEG_BOARD_SERIAL_PORT = _conf['EEG_BOARD_SERIAL_PORT']
EEG_BOARD_ID = _conf['EEG_BOARD_ID']
del _conf


class EEGBrainflow(object):
    def __init__(self, logger=False):
        """ An abstraction of the EEG board and its brainflow interface.
        """
        self.board = self._init_board(logger)  # A brainflow.BoardShim
        self.sample_rate = BoardShim.get_sampling_rate(EEG_BOARD_ID)  # int

        # Channel lists
        self.eeg_channels = BoardShim.get_eeg_channels(EEG_BOARD_ID)
        self.time_channel = BoardShim.get_timestamp_channel(EEG_BOARD_ID)
        self._channel_mask = [self.time_channel] + self.eeg_channels

        # Start OpenBCI_Hub and ensure stays up. If not, address likely in use
        self._bci_hub_proc = Popen([BCI_HUB_PATH], stderr=PIPE, stdout=PIPE)
        time.sleep(1)

        if self._bci_hub_proc.poll() is not None:
            warn(f'Could not start {BCI_HUB_PATH} - It may already be running.')
        else:
            info('Started OpenBCI_Hub.')

        # Set the device to use low latency serial
        Popen(['setserial', EEG_BOARD_SERIAL_PORT, 'low_latency'])
        
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
        """ Prepares the board session and returns True on success, else
            return False.
        """
        try:
            self.board.prepare_session()
        except BrainFlowError:
            error('Failed to get eeg board session. Is it plugged in?')
            return False
        
        return self.board.is_prepared()

    def _do_channel_mask(self, data) -> np.ndarray:
        """ Returns a view of the given board data with only the timestamp
            and eeg data channels.
        """
        try:
            return data[self._channel_mask, :]
        except IndexError:
            try:
                # Data may not contain any columns
                return data[self._channel_mask]
            except IndexError:
                # Data is likely empty
                return data

    def stream_wait(self, seconds) -> np.ndarray:
        """ Blocks for the specified number of seconds before returning an
            np.array of eeg data collected over that time.
        """
        if self._prepare_session():
            self.board.start_stream(EEG_SZ_DATA_BUFF)
            time.sleep(seconds)

            data = self.board.get_board_data()

            self.board.stop_stream()
            self.board.release_session()

            return self._do_channel_mask(data)
