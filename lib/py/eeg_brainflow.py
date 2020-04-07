""" A module for interacting with the application's EEG board via the
    Brainflow API.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import os
import time
import queue
import multiprocessing as mp
from datetime import datetime
from pathlib import Path

import numpy as np

from brainflow.board_shim import BrainFlowError, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations

from lib.py import app


# Config constants
_conf = app.config()
EEG_BOARD_ID = _conf['DEVICE_ID_EEG_BOARD']
EEG_BOARD_SERIAL_PORT = _conf['DEVICE_ID_EEG']
EEG_CSV_DIR = _conf['APP_EEG_EVENTS_CSV_DIR']
del _conf

# Other constants
LOG_FNAME_TEMPLATE = '%Y-%m-%d--%H-%M.csv'
NOTEFILE_FNAME = 'NOTES.md'
SIGNAL_EVENT = True
SIGNAL_STOP = False
SZ_DATA_BUFF = 450000


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
            print('ERROR: Failed to get eeg board session. Is it plugged in?')
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


class EEGAsyncEventLogger(EEGBrainflow):
    def __init__(self, logname, notes='NA', writeback=5, writeafter=5):
        """ # TODO: docstring
        """
        super().__init__()

        # Validate params
        assert(isinstance(logname, str) and isinstance(notes, str))
        assert(writeback > 0 and writeafter > 0)

        if writeback > SZ_DATA_BUFF:
            raise ValueError('Writeback size > data buffer size.')
        if writeafter * self.sample_rate > SZ_DATA_BUFF:
            raise ValueError('Writeafter value too large for data buffer.')

        self._logname = logname
        self._notes = notes
        self._writeback_samples = writeback * self.sample_rate
        self._writeafter_seconds = writeafter

        self._logdir_path = Path(EEG_CSV_DIR, logname + os.path.sep)
        self._async_proc = None
        self._async_queue = None

    def _init_outpath(self):
        """ Sets up the objects output directory by ensuring it exists and
            adding/verifying the notes file.
        """
        notes = self._notes
        output_dir = self._logdir_path
        notefile_path = Path(output_dir, NOTEFILE_FNAME)

        # Create output dir iff not exists
        if not output_dir.exists():
            os.makedirs(output_dir)
            print(f'INFO: Created log dir - {output_dir}')

            # Create note file
            with open(notefile_path, 'w') as f:
                f.writelines(notes)

            note_str = '\t' + '\n\t'.join(notes.split('\n'))
            print(f'INFO: Created log notes - {notefile_path}\n' +
                  f'INFO: Log dir note content -\n{note_str}')
            
        # Else, dir already exists... Use it iff matching notes
        else:
            with open(notefile_path, 'r') as f:
                existing_notes = f.read()

            note_str = '\t' + '\n\t'.join(existing_notes.split('\n'))
            print(f'INFO: Using existing log dir - {output_dir}\n' +
                  f'INFO: Log dir note content -\n{note_str}')

            # Ensure matching notefile content
            if existing_notes != notes:
                raise ValueError(f'Notes mismatch for {notefile_path}')

    def _async_watcher(self, signal_queue):
        """ The async watcher -- intended to be used as a sub process.
            Reads data from the board and, on write signal receive, writes
            the appropriate number of samples to log file. On stop signal
            received, the watcher terminates.
            Note that the watcher may often be watching but not writing, and
            will transition back and forth between watching and watching while
            writing indefiniately until the stop signal is received.
        """
        # Helpers
        def _stop(signal):
            if signal == SIGNAL_STOP:
                print('INFO: Async EEG event watcher STOP received.')
                return True
            return False

        def _event(signal):
            if signal == SIGNAL_EVENT:
                print('INFO: Async EEG event watcher EVENT received...')
                return time.time() + self._writeafter_seconds
            return time.time()
            
        def _do_write(data):
            path = Path(
                self._logdir_path, datetime.now().strftime(LOG_FNAME_TEMPLATE))
            DataFilter.write_file(
                self._do_channel_mask(data), str(path), 'a')

        # Init board session or die
        if not self._prepare_session():
            return

        # Init log dir and begin the data stream
        self._init_outpath()
        self.board.start_stream(SZ_DATA_BUFF)  # Starts async data collection
        signal = None

        print(f'INFO: Async EEG event watcher started at {time.time()}')

        while True:
            # Handle inner loop sig if needed, else wait for new signal
            signal = signal if signal is not None else \
                signal_queue.get()  # blocks

            # Check for kill or unhandled signals
            if _stop(signal):
                break
            elif signal != SIGNAL_EVENT:
                print('ERROR: Async EEG event watcher received unhandled ' +
                    f'signal "{signal}"... Killing async EEG event watcher.')
                break
            
            # If not kill or unhandled signal, start logging the EEG data
            # starting with the specified number of previous data points
            write_until = _event(signal)
            prev_points = self.board.get_board_data()

            if prev_points.shape[1] > 0:
                _do_write(prev_points[:, -self._writeback_samples:])
            else:
                print('WARN: Async watcher has no prev points to write.')

            while time.time() <= write_until:
                print(f'Fr: {time.time()}\nTo: {write_until}\n')

                # Let data accumalte for the specified time then write it out
                time.sleep(self._writeafter_seconds)
                _do_write(self.board.get_board_data())

                # Check for next msg in queue to see if we keep logging
                try:
                    signal = signal_queue.get_nowait()
                except mp.queues.Empty:
                    continue # No msg denotes stop logging -- let loop expire
                
                # Let outter loop handle any signal other than event sig
                if signal != SIGNAL_EVENT:
                    break
                
                # Allow enough time to log another iteration
                else:
                    write_until = _event(signal)
            else:
                signal = None

        # Cleanup
        self.board.stop_stream()
        self.board.release_session()
        print(f'INFO: Async EEG event watcher stopped.')

    def start(self):
        """ Starts the async watcher, putting it in a state where it is ready
            to write accumulated data to the log and is watching for the
            signal to do so.

            :returns: (multiprocessing.Process)
        """
        # If async watcher already running
        if self._async_proc is not None and self._async_proc.is_alive():
            print('ERROR: Async EEG event watcher already running.')

        # Else, not running -- start it
        else:
            ctx = mp.get_context('fork')
            self._async_queue = ctx.Queue(maxsize=1)
            self._async_proc = ctx.Process(
                target=self._async_watcher, args=(self._async_queue,))
            self._async_proc.start()

        return self._async_proc

    def stop(self):
        """ Sends the kill signal to the async watcher.
        """
        try:
            self._async_queue.put_nowait(SIGNAL_STOP)
        except mp.queues.Full:
            # Kick out curr msg and try again
            time.sleep(0.25)
            try:
                _ = self._async_queue.get_nowait()
            except mp.queues.Empty:
                pass
            self._async_queue.put_nowait(SIGNAL_STOP)

    def event(self):
        """ Sends the async watcher the signal to start (or continue) logging,
            starting with the previous number of samples denoted by writeback,
            and ending writeafter number of seconds after the most recent call to this
            function.
        """
        try:
            self._async_queue.put_nowait(SIGNAL_EVENT)
        except mp.queues.Full:
            pass # Don't flood queue with event signals

