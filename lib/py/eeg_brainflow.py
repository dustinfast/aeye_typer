""" A module for interacting with the application's EEG board via the
    Brainflow API.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import os
import time
import multiprocessing as mp
from datetime import datetime
from pathlib import Path

import numpy as np

from brainflow.board_shim import BrainFlowError, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations

from lib.py import app


_conf = app.config()
EEG_BOARD_ID = _conf['DEVICE_ID_EEG_BOARD']
EEG_BOARD_SERIAL_PORT = _conf['DEVICE_ID_EEG']
EEG_CSV_DIR = _conf['APP_EEG_EVENTS_CSV_DIR']
del _conf


class EEGBrainflow():
    def __init__(self, logger=False):
        """ An abstraction of the EEG board and its brainflow interface.
        """
        self.board = self._init_board(logger)  # A brainflow.BoardShim
        self.sample_rate = BoardShim.get_sampling_rate(EEG_BOARD_ID)  # int

        # Channel lists
        self.eeg_channels = BoardShim.get_eeg_channels(EEG_BOARD_ID)
        self.time_channel = BoardShim.get_timestamp_channel(EEG_BOARD_ID)
        self._channel_mask = [self.time_channel] + self.eeg_channels

        self._async_streamer = None  # multiprocessing.Process

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
            print('ERROR: Failed to connect to board. Is dongle plugged in?')
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
            return None # data is likely []

    def _log_stream_async(self, logname, md_notes, seconds=0, write_every=0):
        if not self._prepare_session():
            return

        # If given a write interval, setup writing to file
        if write_every:
            cycle_rate = write_every
            fname_template = '%Y-%m-%d--%H-%M.csv'

            # Denote output dir and ensure exists
            output_dir = Path(EEG_CSV_DIR, logname + os.path.sep) 
            try:
                os.makedirs(output_dir)
            except OSError:
                pass  # Already exists

            # Ensure notes file exists.
            notes_path = Path(output_dir, 'README.md')
            if not notes_path.exists():
                with open(notes_path, 'w') as f:
                    f.writelines(md_notes)
        
        # Else ensure we have a reasonable cycle time
        else:
            cycle_rate = 10
            
        # Begin the stream
        s_time = time.time()
        self.board.start_stream()

        # Get data from the stream at the given interval and do write out
        while True:
            time.sleep(cycle_rate)
            data = self.board.get_board_data()

            if write_every:
                print(self._do_channel_mask(data))
                path = Path(output_dir, datetime.now().strftime(fname_template))
                DataFilter.write_file(
                    self._do_channel_mask(data), str(path), 'a')

            if seconds and time.time() - s_time >= seconds:
                break

        self.board.stop_stream()
        self.board.release_session()


    def log_stream_async(self, logname, md_notes, seconds=20, write_every=10):
        """ Starts an asynchronous logging of eeg data to the application
            output path every WRITE_EVERY seconds, and then quits after the
            given number of seconds (0 denotes never quit).
        """
        if self._async_streamer is not None and self._async_streamer.is_alive():
            print('ERROR: Async stream is already active.')
            return False

        ctx = mp.get_context('spawn')
        p = ctx.Process(
            target=self._log_stream_async, args=(
                logname, md_notes, seconds, write_every))
        p.start()

        print('INFO: Started async stream...')
        return True
        

    def stream_wait(self, seconds, sz_buff=45000) -> np.ndarray:
        """ Blocks for the specified number of seconds before returning an
            np.array of eeg data collected over that time.
        """
        if self._prepare_session():
            self.board.start_stream(sz_buff)
            time.sleep(seconds)

            data = self.board.get_board_data()

            self.board.stop_stream()
            self.board.release_session()

            return self._do_channel_mask(data)
