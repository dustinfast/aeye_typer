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

from pynput.mouse import Button
from pynput.keyboard import Key
from pynput import mouse, keyboard
from brainflow.data_filter import DataFilter

from lib.py import app
from lib.py.eeg_brainflow import EEGBrainflow


# App config constants
_conf = app.config()
LOG_CSV_ROOTDIR = _conf['EVENTLOG_CSV_ROOTDIR']
LOG_CSV_SUBDIR = _conf['EVENTLOG_CSV_SUBDIR']
LOG_EEG_SUBDIR = _conf['EVENTLOG_EEG_SUBDIR']
LOG_KEYS_SUBDIR = _conf['EVENTLOG_KEYS_SUBDIR']
NOTEFILE_FNAME = _conf['EVENTLOG_NOTEFILE_FNAME']
SIGNAL_EVENT = _conf['EVENTLOG_SIGNAL_EVENT']
SIGNAL_STOP = _conf['EVENTLOG_SIGNAL_STOP']
SZ_DATA_BUFF = _conf['EEG_SZ_DATA_BUFF']
del _conf

EEG_CSV_FNAME_TEMPLATE = '%Y-%m-%d--%H-%M.csv'
KEYS_CSV_FNAME_TEMPLATE = '%Y-%m-%d--%H.csv'


###########
# Helpers #
###########


##############
# Class Defs #
##############

class AsyncEEGEventLogger(EEGBrainflow):
    def __init__(
        self, logname, notes='NA', writeback=5, writeafter=5, verbose=True):
        """ A class for performing asynchronous logging of EEG data before
            and after the occurance of an event.
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
        self._verbose = verbose

        self._logdir_path = Path(LOG_CSV_ROOTDIR, logname, LOG_EEG_SUBDIR)
        self._async_proc = None
        self._async_queue = None

    def _init_outpath(self) -> None:
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

    def _async_watcher(self, signal_queue) -> None:
        """ The async watcher -- intended to be used as a sub process.
            Reads data from the board and, on write signal receive, writes
            the appropriate number of samples to log file. On stop signal
            received, the watcher terminates.
            Note that the watcher may often be watching but not writing, and
            will transition back and forth between watching and watching while
            writing indefiniately until the stop signal is received.
        """
        def _stop(signal):
            if signal == SIGNAL_STOP:
                return True
            return False

        def _event(signal):
            if signal == SIGNAL_EVENT:
                return time.time() + self._writeafter_seconds
            return time.time()
            
        def _do_write(data):
            path = Path(
                self._logdir_path, datetime.now().strftime(EEG_CSV_FNAME_TEMPLATE))
            DataFilter.write_file(
                self._do_channel_mask(data), str(path), 'a')

        # Init board session or die
        if not self._prepare_session():
            return

        # Init log dir and begin the data stream
        self._init_outpath()
        self.board.start_stream(SZ_DATA_BUFF)  # Starts async data collection
        signal = None

        if self._verbose:
            print(f'INFO: Async EEG watcher started at {time.time()}')

        while True:
            # Handle inner loop signal if needed, else wait for new signal
            signal = signal if signal is not None else \
                signal_queue.get()  # blocks

            # Check for kill or unhandled signals
            if _stop(signal):
                break
            elif signal != SIGNAL_EVENT:
                if self._verbose:
                    print('WARN: Async EEG watcher received ' +
                          f'unhandled signal "{signal}".')
                signal = None
                continue
            
            # If not kill or unhandled signal, start logging the EEG data
            # starting with the specified number of previous data points
            write_until = _event(signal)
            prev_points = self.board.get_board_data()

            if prev_points.shape[1] > 0:
                _do_write(prev_points[:, -self._writeback_samples:])
            else:
                print('WARN: Async watcher has no prev data to write... ' +
                      'Is it powered on and connected?')

            while time.time() <= write_until:
                # Let data accumulate for the specified time then log it
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

            # If inner loop closed with no kill signal encountered, clear last
            else:
                signal = None


        # Cleanup
        self.board.stop_stream()
        self.board.release_session()

        if self._verbose:
            print(f'INFO: Async EEG watcher stopped.')

    def start(self) -> mp.Process:
        """ Starts the async watcher, putting it in a state where it is ready
            to write accumulated data to the log and is watching for the
            signal to do so.

            :returns: (multiprocessing.Process)
        """
        # If async watcher already running
        if self._async_proc is not None and self._async_proc.is_alive():
            print('ERROR: Async EEG watcher already running.')

        # Else, not running -- start it
        else:
            ctx = mp.get_context('fork')
            self._async_queue = ctx.Queue(maxsize=1)
            self._async_proc = ctx.Process(
                target=self._async_watcher, args=(self._async_queue,))
            self._async_proc.start()

        return self._async_proc

    def stop(self) -> None:
        """ Sends the kill signal to the async watcher.
        """
        try:
            self._async_queue.put_nowait(SIGNAL_STOP)
        except AttributeError:
            print('ERROR: Received STOP but EEG watcher not yet started.')
        except mp.queues.Full:
            if not self._async_proc.is_alive():
                print('ERROR: Received STOP but EEG watcher already stopped.')
            else:
                # Kick out curr msg and try again
                time.sleep(0.25)
                try:
                    _ = self._async_queue.get_nowait()
                except mp.queues.Empty:
                    pass
                self._async_queue.put_nowait(SIGNAL_STOP)

    def event(self) -> None:
        """ Sends the async watcher the signal to start (or continue) logging,
            starting with the previous number of samples denoted by writeback,
            and ending writeafter number of seconds after the most recent call to this
            function.
        """
        try:
            self._async_queue.put_nowait(SIGNAL_EVENT)
        except AttributeError:
            print('ERROR: Received EVENT but EEG eveon_nt watcher not started.')
        except mp.queues.Full:
            if not self._async_proc.is_alive():
                print('ERROR: Received EVENT but EEG watcher is stopped.')
            else:
                pass # No need to flood queue with event signals


class AsyncInputEventLogger(object):
    def __init__(self, logname, notes='NA', on_event_func=None, verbose=True):
        """ A class for asynchronously logging keyboard and mouse input events
            and (optionally) call the given function (no args) when an input
            event occurs.
        """
        # Validate params
        assert(isinstance(logname, str) and isinstance(notes, str))
        assert(on_event_func is None or callable(on_event_func) is True)

        self._logname = logname
        self._notes = notes
        self._on_event = on_event_func
        self._verbose = verbose

        self._logdir_path = Path(LOG_CSV_ROOTDIR, logname, LOG_KEYS_SUBDIR)
        self._async_keywatcher_proc = None
        self._async_mousewatcher_proc = None
        self._shift_down = False

    def _init_outpath(self) -> None:
        """ Sets up the objects output directory by ensuring it exists and
            adding/verifying the notes file.
        """
        notes = self._notes
        output_dir = self._logdir_path
        notefile_path = Path(output_dir, NOTEFILE_FNAME)

        # Create output dir iff not exists
        if not output_dir.exists():
            os.makedirs(output_dir)

            if self._verbose:
                print(f'INFO: Created log dir - {output_dir}')

            # Create note file
            with open(notefile_path, 'w') as f:
                f.writelines(notes)

            note_str = '\t' + '\n\t'.join(notes.split('\n'))
            
            if self._verbose:
                print(f'INFO: Created log notes - {notefile_path}\n' +
                      f'INFO: Log dir note content -\n{note_str}')
            
        # Else, dir already exists... Use it iff matching notes
        else:
            with open(notefile_path, 'r') as f:
                existing_notes = f.read()

            note_str = '\t' + '\n\t'.join(existing_notes.split('\n'))

            if self._verbose:
                print(f'INFO: Using existing log dir - {output_dir}\n' +
                      f'INFO: Log dir note content -\n{note_str}')

            # Ensure matching notefile content
            if existing_notes != notes:
                raise ValueError(f'Note mismatch for {notefile_path}')

    def _do_on_event_call(self):
        """ Calls the user-defined on_event function iff its defined.
        """
        if self._on_event is not None:
            self._on_event()

    def _log_keys_event(self, key, pressed):
        """ Logs the given key press/release event to file.
        """
        t = time.time()
        self._do_on_event_call()

        if self._verbose:
            print(f'KEY EVENT: {t}, {key}, {pressed}')

    def _log_mouse_event(self, btn, pressed, x, y):
        """ Logs the given button press/release event to file.
            Note: if btn is scroll, pressed = 1 for scroll_up and -1 for
            scroll_down
        """
        t = time.time()
        self._do_on_event_call()
        
        if self._verbose:
            print(f'MOUSE EVENT: {t}, {btn}, {pressed}, ({x}, {y})')

    def _on_click(self, x, y, button, pressed):
        """ Mouse click callback, for use by the async listener."""
        self._log_mouse_event(button, pressed, x, y)
            
    def _on_scroll(self, x, y, dx, dy):
        """ Mouse scroll callback, for use by the async listener."""
        self._log_mouse_event('scroll', dy, x, y)
        
    def _on_press(self, key):
        """ Keyboard key-press callback, for use by the async listener."""
        self._log_keys_event(key, True)

        # Note shift-key status, for exit keycode purposes
        if key == keyboard.Key.shift:
            self._shift_down = True

    def _on_release(self, key):
        """ Keyboard key-release callback, for use by the async listener."""
        self._log_keys_event(key, False)

        # Note shift-key status and check for STOP key combo
        if key == keyboard.Key.shift:
            self._shift_down = False

        if key == keyboard.Key.esc and self._shift_down:
            return False  # Shutdown listener

    def start(self) -> None:
        """ Starts the async keyboard/mouse loggers (if not already running) 
            and returns a process ref that the user may join() on.
        """
        m = self._async_mousewatcher_proc
        k = self._async_keywatcher_proc

        self._init_outpath()

        # If mouse watcher already running
        if m and m.is_alive():
            print('ERROR: Async mouse watcher already running.')

        # Else, mouse watcher not running -- start it
        else:
            self._async_mousewatcher_proc = mouse.Listener(
                on_click=self._on_click, on_scroll=self._on_scroll)
            self._async_mousewatcher_proc.start()
            
            if self._verbose:
                print(f'INFO: Async mouse watcher started.')

        # If keyboard watcher already running
        if k and k.is_alive():
            print('ERROR: Async keyboard watcher already running.')

        # Else, key watcher not running -- start it
        else:
            self._async_keywatcher_proc = keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release)
            self._async_keywatcher_proc.start()
            
            if self._verbose:
                print(f'INFO: Async keyboard watcher started.')

        # Only return the keyb proc, because it watches for STOP keystrokes
        return self._async_keywatcher_proc
