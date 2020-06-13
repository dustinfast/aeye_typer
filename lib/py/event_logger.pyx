#cython: language_level=3
""" A module for logging EEG, Gaze, and Keyboard/Mouse Events to CSV file.
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
from brainflow.data_filter import DataFilter

from lib.py.app import config, info, info_ok, warn, error
from lib.py.eeg_brainflow import EEGBrainflow
from lib.py.eyetracker_gaze import EyeTrackerGaze


# App config constants
_conf = config()
LOG_RAW_ROOTDIR = _conf['EVENTLOG_RAW_ROOTDIR']
LOG_EEG_SUBDIR = _conf['EVENTLOG_EEG_SUBDIR']
LOG_KEYB_SUBDIR = _conf['EVENTLOG_KEYB_SUBDIR']
LOG_GAZE_SUBDIR = _conf['EVENTLOG_GAZE_SUBDIR']
LOG_MOUSE_SUBDIR = _conf['EVENTLOG_MOUSE_SUBDIR']
NOTEFILE_FNAME = _conf['EVENTLOG_NOTEFILE_FNAME']
SZ_DATA_BUFF = _conf['EEG_SZ_DATA_BUFF']
del _conf

# MP queue signals
SIGNAL_EVENT = True
SIGNAL_STOP = False

class EventLogger(object):
    def __init__(self, logname, notes, verbose):
        """ An event logger parent class. Contains logfile paths/attributes.
            # TODO: Refactor as EventLog?
        """
        assert(isinstance(logname, str))
        assert(isinstance(notes, (str, type(None))))
        assert(isinstance(verbose, bool))

        self._name = logname
        self._notes = notes
        self._verbose = verbose
        self._logdir_path = None

    def _init_outpath(self, sub_dirs=[]) -> None:
        """ Sets up the log output directory by ensuring it exists and
            adding/verifying the notes file.

            :param sub_dirs: (list) One or more sub-directories to create,
            relative to the loggers root directory.
        """
        self._logdir_path = Path(LOG_RAW_ROOTDIR, self._name)

        notes = self._notes
        output_dir = self._logdir_path
        notefile_path = Path(output_dir, NOTEFILE_FNAME)

        # Create output dirs iff not exists
        if not output_dir.exists():
            os.makedirs(output_dir)

            for d in sub_dirs:
                os.makedirs(Path(output_dir, d))

            if self._verbose:
                info(f'Created log dir - {output_dir}')

            # Create note file
            if self._notes:
                with open(notefile_path, 'w') as f:
                    f.writelines(notes)

                note_str = '\t' + '\n\t'.join(notes.split('\n'))
                
                if self._verbose:
                    info(f'Created log notes - {notefile_path}')
                    info(f'Log dir note content -\n{note_str}')
            
        # Else, dir already exists... Use it iff matching notes
        else:
            info(f'Using existing log dir - {output_dir}')

            # Ensure subdirs also exist
            for d in sub_dirs:
                p = Path(output_dir, d)
                os.makedirs(Path(output_dir, d)) if not p.exists() else None

            try:
                with open(notefile_path, 'r') as f:
                    existing_notes = f.read()
            except FileNotFoundError:
                if self._notes:
                    raise ValueError(f'Note mismatch for {notefile_path}')
                else:
                    pass  # Expected
            else:
                note_str = '\t' + '\n\t'.join(existing_notes.split('\n'))

                if self._verbose:
                    info(f'Log dir note content -\n{note_str}')

                # Ensure matching notefile content
                if not self._notes or existing_notes != notes:
                    raise ValueError(f'Note mismatch for {notefile_path}')

    def start(self):
        raise NotImplementedError  # Child classes must override

    def stop(self):
        raise NotImplementedError  # Child classes must override
    

class AsyncEEGEventLogger(EventLogger, EEGBrainflow):
    _LOG_EEG_FNAME_TEMPLATE = '%Y-%m-%d--%H-%M.csv'

    def __init__(self, name, notes, writeback=5, writeafter=5, verbose=True):
        """ A class for performing asynchronous logging of EEG data to CSV
            before and after the occurance of receipt of an event signal.
        """
        EEGBrainflow.__init__(self)
        EventLogger.__init__(self, name, notes, verbose)

        assert(writeback > 0 and writeafter > 0)

        if writeback > SZ_DATA_BUFF:
            raise ValueError('Writeback size > data buffer size.')
        if writeafter * self.sample_rate > SZ_DATA_BUFF:
            raise ValueError('Writeafter value too large for data buffer.')

        self._writeback_samples = writeback * self.sample_rate
        self._writeback_seconds = writeback
        self._writeafter_seconds = writeafter
        self._stream_start_time = None

        self._async_proc = None
        self._async_queue = None

    def _async_watcher(self, signal_queue) -> None:
        """ The async watcher -- intended to be used as a sub process.
            Reads data from the board and, on write signal receive, writes
            the appropriate number of samples to log file. On stop signal
            received, the watcher terminates.
            Note that the watcher may often be watching but not writing, and
            will transition back and forth between watching and watching while
            writing indefinately until the stop signal is received.
        """
        def _stop(signal):
            if signal == SIGNAL_STOP:
                if self._verbose:
                    info(f'EEG watcher received STOP at {time.time()}s.')
                return True

            return False

        def _event(signal):
            if signal == SIGNAL_EVENT:
                return time.time() + self._writeafter_seconds
            return time.time()
            
        def _log_insert_line(line, t, path):
            """ Writes a line to the log denoting the stream start or stop time.
                This is necessary because the timestamp in the log for each
                sample is based on when the sample was received by the system,
                vs actual time it was generated. Therefore the actual timestamp
                must must later be inferred (in post-processing) from these 
                start/stop times.
            """
            with open(path, 'a') as f:
                f.write(f'{line}: {t}\n')

        def _do_write(data, start_time, end_time):
            path = Path(
                self._logdir_path, LOG_EEG_SUBDIR, datetime.now().strftime(
                    self._LOG_EEG_FNAME_TEMPLATE))

            # Warn if data is empty
            if data.shape[1] <= 0:
                _log_insert_line('EMPTY', time.time(), path)

                warn('No EEG watcher data to write.. Attempting reconnect.')

                self.board.stop_stream()
                self.board.release_session()
                
                if not self._prepare_session():
                    error('EEG watcher failed to reconnect.')
                    _log_insert_line('RECONNECT FAILED', time.time(), path)

                self.board.start_stream(SZ_DATA_BUFF) 
                self._stream_start_time = time.time()   
                time.sleep(0.25)

                if self.board.get_board_data_count() <= 0:
                    error('EEG watcher failed to reconnect.')
                    _log_insert_line('RECONNECT FAILED', time.time(), path)
                else:
                    info_ok('EEG watcher reconnected successfully.')
                    _log_insert_line('RECONNECTED', time.time(), path)
                
                return

            _log_insert_line('START_OF_BLOCK', start_time, path)

            DataFilter.write_file(
                self._do_channel_mask(data), str(path), 'a')

            _log_insert_line('END_OF_BLOCK', end_time, path)

            if self._verbose:
                info(f'Wrote eeg log to {path}')

        # Init board session or die
        if not self._prepare_session():
            error(f'EEG watcher failed to get EEG board session.')
            return

        # Begin the data stream
        self.board.start_stream(SZ_DATA_BUFF)  # Async, does not block
        self._stream_start_time = time.time()
        signal = None

        info(f'EEG watcher started at {time.time()}s.')

        while True:
            # Handle inner loop signal if needed, else wait for new signal
            signal = signal if signal is not None else \
                signal_queue.get()  # blocks

            # Check for kill or unhandled signals
            if _stop(signal):
                break

            elif signal != SIGNAL_EVENT:
                warn(f'EEG watcher received unhandled signal "{signal}".')
                signal = None
                continue
            
            # If not kill or unhandled signal, start logging the EEG data
            # starting with the specified number of previous data points
            write_until = _event(signal)
            prev_points = self.board.get_board_data()

            if prev_points.shape[1] > 0:
                # Determine if chunk start time is stream start time, or earlier
                if self._stream_start_time and time.time() - \
                        self._stream_start_time < self._writeback_seconds:
                            start_time = self._stream_start_time
                else:
                    start_time = time.time() - self._writeback_seconds
                    self._stream_start_time = None

                _do_write(prev_points[:, -self._writeback_samples:],
                          start_time,
                          time.time())
            else:
                error('EEG watcher has no prev data to write. Is it connected?')

            while time.time() <= write_until:
                # Let data accumulate for the specified time then write to file
                start_time = time.time()
                time.sleep(self._writeafter_seconds)
                _do_write(self.board.get_board_data(),
                          start_time,
                          time.time())

                # Check for next msg in queue to see if we keep logging
                try:
                    signal = signal_queue.get_nowait()
                except mp.queues.Empty:
                    continue # No msg denotes stop logging -- let loop expire
                
                # Let outter loop handle any signal other than event sig
                if signal != SIGNAL_EVENT:
                    break
                
                # Signal event receiverd, so log for another iteration
                else:
                    write_until = _event(signal)

            # If inner loop closed & not kill signal, reset & return to outter
            else:
                signal = None

        # Cleanup
        self.board.stop_stream()
        self.board.release_session()

        info(f'EEG watcher stopped at {time.time()}s.')

    def start(self) -> mp.Process:
        """ Starts the async watcher, putting it in a state where it is ready
            to write accumulated data to the log and is watching for the
            signal to do so.

            :returns: (multiprocessing.Process)
        """
        # If async watcher already running
        if self._async_proc is not None and self._async_proc.is_alive():
            warn('EEG watcher already running.')

        # Else, not running -- start it
        else:
            self._init_outpath([LOG_EEG_SUBDIR])

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
            info(f'EEG watcher sending stop A at {time.time()}s.') # debug
        except AttributeError:
            error('Received STOP but EEG watcher not yet started.')
        except mp.queues.Full:
            if not self._async_proc.is_alive():
                error('Received STOP but EEG watcher already stopped.')
            else:
                # Kick out curr msg and try again
                time.sleep(0.25)
                try:
                    _ = self._async_queue.get_nowait()
                except mp.queues.Empty:
                    pass
                self._async_queue.put_nowait(SIGNAL_STOP)
                info(f'EEG watcher sending stop B at {time.time()}s.') # debug

    def event(self) -> None:
        """ Sends the async watcher the signal to start (or continue) logging,
            starting with the previous number of samples denoted by writeback,
            and ending writeafter number of seconds after the most recent call
            to this function.
        """
        try:
            self._async_queue.put_nowait(SIGNAL_EVENT)
        except AttributeError:
            error('Received EVENT but EEG watcher not started.')
        except mp.queues.Full:
            if not self._async_proc.is_alive():
                error('Received EVENT but EEG watcher is stopped.')
            else:
                pass # No need to flood queue with event signals


class AsyncGazeEventLogger(EventLogger):
    _LOG_GAZE_FNAME_TEMPLATE = '%Y-%m-%d--%H-%M.csv'

    def __init__(self, name, notes, writeback=5, writeafter=5, verbose=True):
        """ A class for performing asynchronous logging of gaze data to CSV
            before and after the occurance of receipt of an event signal.
        """
        assert(writeback > 0 and writeafter > 0)
        EventLogger.__init__(self, name, notes, verbose)

        self.eyetracker = EyeTrackerGaze()
        self.sample_rate = self.eyetracker.sample_rate

        if writeback > SZ_DATA_BUFF:
            raise ValueError('Writeback size > data buffer size.')
        if writeafter * self.sample_rate > SZ_DATA_BUFF:
            raise ValueError('Writeafter value too large for data buffer.')
        self._writeback_samples = writeback * self.sample_rate
        self._writeafter_seconds = writeafter

        self._async_proc = None
        self._async_queue = None

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
            s = self.eyetracker.gaze_data_sz() 
            if self.eyetracker.gaze_data_sz() <= 0:
                error('Gaze watcher has no data to write.')
                return

            path = Path(
                self._logdir_path, LOG_GAZE_SUBDIR, datetime.now().strftime(
                    self._LOG_GAZE_FNAME_TEMPLATE))
            self.eyetracker.to_csv(str(path), self._writeback_samples)

            if self._verbose:
                info(f'Wrote gaze log sz {s}to {path}')

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
            info('Gaze watcher already running.')

        # Else, not running -- start it
        else:
            self._init_outpath([LOG_GAZE_SUBDIR])

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
            info(f'Gaze watcher sending stop A at {time.time()}s.') # debug

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
                info(f'Gaze watcher sending stop B at {time.time()}s.') # debug


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


class AsyncInputEventLogger(EventLogger):
    _DF_MAXROWS = 2500

    _LOG_KEYS_FNAME_TEMPLATE = 'keys-%Y-%m-%d--%H.csv'
    _LOG_KEYS_COLS = [('time', np.float64), 
                      ('keycode', np.int32), 
                      ('pressed', np.bool_)]

    _LOG_MOUSE_FNAME_TEMPLATE = 'mouse-%Y-%m-%d--%H.csv'
    _LOG_MOUSE_COLS = [('time', np.float64),
                       ('keycode', np.int32),
                       ('pressed', np.bool_),
                       ('x', np.int32),
                       ('y', np.int32)]

    def __init__(self, name, notes, callbacks=[], verbose=True):
        """ A class for asynchronously logging keyboard and mouse input events
            to CSV and (optionally) calling the given function (w/no args)
            when an input event occurs.
        """
        assert(isinstance(callbacks, list))
        super().__init__(name, notes, verbose)

        self._callbacks = callbacks
        self._shift_down = False

        self._async_keywatcher_proc = None
        self._async_mousewatcher_proc = None
        
        self._df_keylog_idx = 0
        self._df_mouselog_idx = 0
        self._df_keylog = self._new_log_df(self._LOG_KEYS_COLS)
        self._df_mouselog = self._new_log_df(self._LOG_MOUSE_COLS)

    def _do_callbacks(self):
        """ Calls the user-defined on_event callbacks, if any.
        """
        [f() for f in self._callbacks if callable(f)]

    def _new_log_df(self, column_defs):
        """ Returns a new zero-filled pd.DataFrame having the given columns.
        """
        return pd.DataFrame(
            np.zeros(self._DF_MAXROWS, dtype=np.dtype(column_defs)))

    def _append_df_row(self, df, idx, row):
        """ Appends the given row to the given df at the row denoted by idx
            and returns the next row's insertion idx.
        """
        df.iloc[idx, :] = row
        idx += 1

        return idx

    def _write_log(self, df, idx, log_subdir, fname_template, column_defs):
        """ Returns the idx of the next row to write. If the df's capacity
            has been reached, also writes the contents to file and resets
            the df's contents.
        """
        # Write df to file and then zero-fill its contents
        if idx >= self._DF_MAXROWS:
            path = Path(
                self._logdir_path, log_subdir, datetime.now().strftime(
                    fname_template))

            # Write to new file with no col headers
            if not os.path.exists(path):
                df.to_csv(path, index=False, mode='w', header=False)
            
            # OR, Append to existing file with no col headers
            else:
                df.to_csv(path, index=False, mode='a', header=False)
                
            for col in df.columns:
                df[col].values[:] = 0
            idx = 0

            if self._verbose:
                info(f'Wrote {log_subdir} log to {path}')

        return idx

    def _log_key_event(self, key, pressed):
        """ Adds the given key press/release event to the keystroke df. When
            the df gets full it is written to file and cleared.
        """
        t_stamp = time.time()
        self._do_callbacks()

        # Convert the Key obj to its ascii value
        try:
            key_id = ord(key.char.lower())
        
        # OR, convert the Key object to it's x11 code
        except AttributeError:
            try:
                key_id = key.value.vk
            except AttributeError:
                key_id = key.vk

        # Update the df and (iff needed) write to file
        idx = self._append_df_row(self._df_keylog,
                                  self._df_keylog_idx,
                                  [t_stamp, key_id, pressed])
        self._df_keylog_idx = self._write_log(self._df_keylog,
                                              idx,
                                              LOG_KEYB_SUBDIR,
                                              self._LOG_KEYS_FNAME_TEMPLATE,
                                              self._LOG_KEYS_COLS)

    def _log_mouse_event(self, btn_id, pressed, x, y):
        """ Adds the given key press/release event to the keystroke df. When
            the df gets full it is written to file and then cleared. Note that
            btn_ids are 1 = left, 2 = middle, right = 3, 4 = scrollwheel, and
            0 = unknown. If event is a mouse scroll event, pressed = 1 for 
            scroll_up and -1 for scroll_down.
        """
        t_stamp = time.time()
        self._do_callbacks()
        
        # Update the df and (iff needed) write to file
        idx = self._append_df_row(self._df_mouselog,
                                  self._df_mouselog_idx,
                                  [t_stamp, btn_id, pressed, x, y])
        self._df_mouselog_idx = self._write_log(self._df_mouselog,
                                              idx,
                                              LOG_MOUSE_SUBDIR,
                                              self._LOG_MOUSE_FNAME_TEMPLATE,
                                              self._LOG_MOUSE_COLS)

    def _on_click(self, x, y, button, pressed):
        """ Mouse click callback, for use by the async listener."""
        self._log_mouse_event(button.value, pressed, x, y)
            
    def _on_scroll(self, x, y, dx, dy):
        """ Mouse scroll callback, for use by the async listener."""
        self._log_mouse_event(4, dy, x, y)
        
    def _on_press(self, key):
        """ Keyboard key-press callback, for use by the async listener."""
        self._log_key_event(key, True)

        # Denote shift-key status, for exit keycode purposes
        if key == keyboard.Key.shift: self._shift_down = True

    def _on_release(self, key):
        """ Keyboard key-release callback, for use by the async listener."""
        # Only log release of special chars
        if not (key == keyboard.Key.shift or key == keyboard.Key.alt or 
            key == keyboard.Key.ctrl or key == keyboard.Key.esc):
                return

        self._log_key_event(key, False)

        # Denote shift-key status and check for STOP key combo
        if key == keyboard.Key.shift: self._shift_down = False

        if key == keyboard.Key.esc and self._shift_down:
            # if self._verbose: # debug
            info(f'Input watcher received STOP at {time.time()}s.')

            # Write contents of any existing data
            self._write_log(self._df_keylog.iloc[:self._df_keylog_idx, :],
                            self._DF_MAXROWS,
                            LOG_KEYB_SUBDIR,
                            self._LOG_KEYS_FNAME_TEMPLATE,
                            self._LOG_KEYS_COLS)
            self._write_log(self._df_mouselog.iloc[:self._df_mouselog_idx, :],
                            self._DF_MAXROWS,
                            LOG_MOUSE_SUBDIR,
                            self._LOG_MOUSE_FNAME_TEMPLATE,
                            self._LOG_MOUSE_COLS)
            return False

    def start(self) -> None:
        """ Starts the async keyboard/mouse loggers (if not already running) 
            and returns a process ref that the user may join() on.
        """
        m = self._async_mousewatcher_proc
        k = self._async_keywatcher_proc

        self._init_outpath([LOG_KEYB_SUBDIR, LOG_MOUSE_SUBDIR])

        # If mouse watcher already running
        if m and m.is_alive():
            warn('Mouse watcher already running.')

        # Else, mouse watcher not running -- start it
        else:
            self._async_mousewatcher_proc = mouse.Listener(
                on_click=self._on_click, on_scroll=self._on_scroll)

            self._async_mousewatcher_proc.start()
            
            info(f'Mouse watcher started at {time.time()}s.')

        # If keyboard watcher already running
        if k and k.is_alive():
            warn('Keyboard watcher already running.')

        # Else, key watcher not running -- start it
        else:
            self._async_keywatcher_proc = keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release)
            self._async_keywatcher_proc.start()
            
            info(f'Keyboard watcher started at {time.time()}s.')

        # Give the threads time to spin up
        time.sleep(2)

        # Only return the keyb proc, because it watches for STOP keystrokes.
        # The user may join() on this proc if desired
        return self._async_keywatcher_proc
