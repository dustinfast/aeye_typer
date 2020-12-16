#cython: language_level=3
""" A module for logging Gaze, and Keyboard/Mouse Events to CSV file.
"""
__author__ = 'Dustin Fast [dustin.fast@outlook.com], 2020'

import os
import time
import queue
import multiprocessing as mp
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from pynput.mouse import Button
from pynput.keyboard import Key
from pynput import mouse, keyboard

from lib.py.app import key_to_id, app_config, info, warn, error, bold
from lib.py.eyetracker_gaze import EyeTrackerGaze


LOG_RAW_ROOTDIR = app_config('EVENTLOG_RAW_ROOTDIR')
GAZE_WRITEBACK = app_config('EYETRACKER_WRITEBACK_SECONDS')
GAZE_WRITEAFTER = app_config('EYETRACKER_WRITEAFTER_SECONDS')
GAZE_SAMPLE_RATE = app_config('EYETRACKER_SAMPLE_HZ')
GAZE_BUFF_SZ = app_config('EYETRACKER_BUFF_SZ')

# MP queue signals
SIGNAL_EVENT = True
SIGNAL_STOP = False


class AsyncGazeEventLogger(object):
    def __init__(self, logpath, verbose=False):
        """ A class for performing asynchronous logging of gaze data to CSV.
            The logging occurs GAZE_WRITEBACK/GAZE_WRITEAFTER seconds before/
            after receipt of an event signal.
        """
        # Validate writeback/after elements
        if GAZE_WRITEBACK <= 0 or GAZE_WRITEAFTER <= 0:
            raise ValueError('Writeback/Writeafter must be > 0.')
        elif GAZE_WRITEBACK > GAZE_BUFF_SZ:
            raise ValueError('Writeback size > data buffer size.')
        elif GAZE_WRITEAFTER * GAZE_SAMPLE_RATE > GAZE_BUFF_SZ:
            raise ValueError('Writeafter value too large for data buffer.')

        self._logpath = str(logpath)
        self._verbose = verbose
        
        self._writeback_samples = GAZE_WRITEBACK * GAZE_SAMPLE_RATE
        self._writeafter_seconds = GAZE_WRITEAFTER

        self._async_proc = None
        self._async_queue = None

        self.eyetracker = EyeTrackerGaze()
        
    def _async_watcher(self, signal_queue) -> None:
        """ The async watcher -- intended to be used as a sub process.
            Reads data from the eyetracker and, on write signal receive, writes
            the appropriate number of samples to log file. On stop signal
            received, the watcher terminates.
            Note that the watcher may often be watching but not writing, and
            will transition back and forth between watching and watching while
            writing indefinately until the stop signal is received.
        """
        def _stop(signal):
            if signal == SIGNAL_STOP:
                if self._verbose:
                    info(f'Gaze watcher received STOP at {time.time()}s.')
                return True

            return False

        def _event(signal):
            if signal == SIGNAL_EVENT:
                return time.time() + self._writeafter_seconds
            return time.time()
            
        def _do_write():
            if self.eyetracker.gaze_data_sz() <= 0:
                error('Attempted Gaze watcher log write but no data available.')
                return

            self.eyetracker.to_csv(self._logpath, self._writeback_samples)

            if self._verbose:
                print(f'Wrote to gaze log at {self._logpath}')

        # Start the eyetrackers asynchronous data stream
        self.eyetracker.open()
        self.eyetracker.start()
        signal = None

        info(f'Gaze watcher started at {time.time()}s.')

        while True:
            # Handle inner loop signal if needed, else wait for new signal
            signal = signal if signal is not None else \
                signal_queue.get()  # blocks

            # Check for kill or unhandled signals
            if _stop(signal):
                break
            elif signal != SIGNAL_EVENT:
                if self._verbose:
                    warn(f'Gaze watcher received unhandled signal "{signal}".')
                signal = None
                continue
            
            # If not kill or unhandled signal, start writing the gaze data
            # starting with the specified number of previous data points
            write_until = _event(signal)

            if self.eyetracker.gaze_data_sz() >= 0:
                _do_write()
            else:
                error('Gaze watcher has no prev data to write. Is it connected?')

            while time.time() <= write_until:
                # Let data accumulate for the specified time then log it
                time.sleep(self._writeafter_seconds)
                _do_write()

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

        # If here, kill signal received. Do cleanup...
        self.eyetracker.stop()
        self.eyetracker.close()

        info(f'Gaze watcher stopped at {time.time()}s.')

    def start(self) -> mp.Process:
        """ Starts the async watcher, putting it in a state where it is ready
            to write accumulated data to the log and is watching for the
            signal to do so.

            :returns: (multiprocessing.Process)
        """
        # If async watcher already running
        if self._async_proc is not None and self._async_proc.is_alive():
            warn('Gaze watcher received START but already running.')

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
            error('Received STOP but Gaze watcher not yet started.')
        except mp.queues.Full:
            if not self._async_proc.is_alive():
                error('Received STOP but Gaze watcher already stopped.')
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
            and ending writeafter number of seconds after the most recent call
            to this function.
        """
        try:
            self._async_queue.put_nowait(SIGNAL_EVENT)
        except AttributeError:
            error('Received EVENT but Gaze watcher not started.')
        except mp.queues.Full:
            if not self._async_proc.is_alive():
                error('Received EVENT but Gaze watcher is stopped.')
            else:
                pass # No need to flood queue with event signals


class AsyncMouseClkEventLogger(object):
    _DF_MAXROWS = 2500

    _LOG_MOUSE_COLS = [('time', np.float64),
                       ('keycode', np.int32),
                       ('x', np.int32),
                       ('y', np.int32)]

    def __init__(self, logpath, callbacks=[], verbose=False):
        """ A class for asynchronously logging mouse input events
            to CSV and (optionally) calling the given callbacks (w/no args)
            when an input event occurs.
        """
        assert(isinstance(callbacks, list))

        self._logpath = str(logpath)
        self._verbose = verbose
        
        self._callbacks = callbacks
        self._shift_down = False

        self._async_keywatcher_proc = None
        self._async_mousewatcher_proc = None
        
        self._df_mouselog_idx = 0
        self._df_mouselog = pd.DataFrame(
            np.zeros(self._DF_MAXROWS, dtype=np.dtype(self._LOG_MOUSE_COLS)))

    def _do_callbacks(self):
        """ Calls the user-defined on_event callbacks, if any.
        """
        [f() for f in self._callbacks if callable(f)]

    def _append_df_row(self, df, idx, row):
        """ Appends the given row to the given df at the row denoted by idx
            and returns the next row's insertion idx.
        """
        df.iloc[idx, :] = row
        idx += 1

        return idx

    def _write_log(self, df, idx):
        """ Returns the idx of the next row to write. If the df's capacity
            has been reached, also writes the contents to file and resets
            the df's contents.
        """
        # Write df to file and then re-create it
        if idx >= self._DF_MAXROWS:
            path = self._logpath

            # Write to new file with no col headers
            if not os.path.exists(path):
                df.to_csv(path, index=False, mode='w', header=False)
            
            # OR, Append to existing file with no col headers
            else:
                df.to_csv(path, index=False, mode='a', header=False)
            
            # Zero-fill df, effectively re-creating
            for col in df.columns:
                df[col].values[:] = 0
            idx = 0

            if self._verbose:
                print(f'Wrote mouse-click log to {path}')

        return idx

    def _on_click(self, x, y, button, pressed):
        """ Mouse click callback, for use by the async listener."""
        # Log down-clicks
        if pressed:
            t_stamp = time.time()
            self._do_callbacks()
            
            # Update the log/df and (iff needed) write to file
            idx = self._append_df_row(self._df_mouselog,
                                      self._df_mouselog_idx,
                                      [t_stamp, button.value, x, y])
            self._df_mouselog_idx = self._write_log(self._df_mouselog, idx)
        
    def _on_keypress(self, key):
        """ Keyboard key-press callback, for use by the async listener."""
        # Denote shift-key status, for exit keycode purposes
        if key == keyboard.Key.shift: self._shift_down = True

    def _on_keyrelease(self, key):
        """ Keyboard key-release callback, for use by the async listener."""
        # Check for exit keycode
        if key != keyboard.Key.shift and key != keyboard.Key.esc:
                return

        # Denote shift-key status
        if key == keyboard.Key.shift: self._shift_down = False

        # Stop logging iff STOP key combo detected
        if key == keyboard.Key.esc and self._shift_down:
            if self._verbose:
                info(f'Input watcher received STOP at {time.time()}s.')

            # Write contents of any existing data
            self._write_log(self._df_mouselog.iloc[:self._df_mouselog_idx, :],
                            self._DF_MAXROWS)
            return False

    def start(self) -> None:
        """ Starts the async keyboard/mouse watchers (if not already running) 
            and returns a process ref that the user may join() on.
        """
        m = self._async_mousewatcher_proc
        k = self._async_keywatcher_proc

        # If mouse watcher already running
        if m and m.is_alive():
            warn('Mouse watcher already running.')

        # Else, mouse watcher not running -- start it
        else:
            self._async_mousewatcher_proc = mouse.Listener(
                on_click=self._on_click)
            self._async_mousewatcher_proc.start()
            
            info(f'Mouse watcher started at {time.time()}s.')

        # If keyboard watcher already running
        if k and k.is_alive():
            warn('Keyboard watcher already running.')

        # Else, key watcher not running -- start it
        else:
            self._async_keywatcher_proc = keyboard.Listener(
                on_press=self._on_keypress, on_release=self._on_keyrelease)
            self._async_keywatcher_proc.start()
            
            info(f'Keyboard watcher started at {time.time()}s.')

        # Give the threads time to spin up
        time.sleep(2)

        bold('\nRunning... Press SHIFT + ESC to terminate.\n')

        # Only return the keyb proc, because it watches for STOP keystrokes.
        # The user may join() on this proc if desired
        return self._async_keywatcher_proc
