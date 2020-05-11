""" Misc data manipulation helpers.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

from pathlib import Path

import pandas as pd

from lib.py.app import config, info, info_ok, warn, error
from lib.py.eeg_brainflow import EEGBrainflow
from lib.py.eyetracker_gaze import EyeTrackerGaze


# App config constants
_conf = config()
LOG_ROOTDIR = _conf['EVENTLOG_ROOTDIR']
LOG_EEG_SUBDIR = _conf['EVENTLOG_EEG_SUBDIR']
LOG_GAZE_SUBDIR = _conf['EVENTLOG_GAZE_SUBDIR']
LOG_KEYB_SUBDIR = _conf['EVENTLOG_KEYB_SUBDIR']
LOG_MOUSE_SUBDIR = _conf['EVENTLOG_MOUSE_SUBDIR']
EVENTLOG_EEG_COLS = _conf['EVENTLOG_EEG_COLS']
EVENTLOG_GAZE_COLS = _conf['EVENTLOG_GAZE_COLS']
EVENTLOG_KEYB_COLS = _conf['EVENTLOG_KEYB_COLS']
EVENTLOG_MOUSE_COLS = _conf['EVENTLOG_MOUSE_COLS']
del _conf


def files_in_dir(path):
    """ Returns a list of path objects representing the files contained in the
        top level of the given directory.
    """
    return [child for child in path.iterdir() if not child.is_dir()]

def pd_from_csvs(paths, names=None):
    """ Like pd.to_csv, but for multiple csv files and with header=None.
    """
    dfs = []

    [dfs.append(
        pd.read_csv(
            p, index_col=None, header=None, names=names)
        ) for p in paths
    ]

    return pd.concat(dfs, axis=0, ignore_index=True, names=names)


class EventLog(object):
    def __init__(self, logs):
        """ The parent abstraction of the combined EEG, Gaze, Key, and Mouse
            event log files contained in the given log(s).

            ASSUMES: Strict adherence to data directory format.
            
            :param logs: ([str]) A list of log names.
        """
        self._root_paths = []           # Paths to each of the base log dirs
        self._raw_eeg_paths = []        # Paths to each eeg-log in all logs
        self._raw_gaze_paths = []       # ...
        self._raw_keyb_paths = []
        self._raw_mouse_paths = []

        # Populate root paths
        [self._root_paths.append(Path(LOG_ROOTDIR, log)) for log in logs]

        # Populate raw (i.e., csv) paths and sort by file name
        for p in self._root_paths:
            try:
                self._raw_eeg_paths += files_in_dir(Path(p, LOG_EEG_SUBDIR))
            except FileNotFoundError:
                warn(f'Failed to iterate EEG logs for {p.name}.')

            try:
                self._raw_gaze_paths += files_in_dir(Path(p, LOG_GAZE_SUBDIR))
            except FileNotFoundError:
                warn(f'Failed to iterate Gaze logs for {p.name}.')

            try:
                self._raw_keyb_paths += files_in_dir(Path(p, LOG_KEYB_SUBDIR))
            except FileNotFoundError:
                warn(f'Failed to iterate Keyb logs for {p.name}.')

            try:
                self._raw_mouse_paths += files_in_dir(Path(p, LOG_MOUSE_SUBDIR))
            except FileNotFoundError:
                warn(f'Failed to iterate Mouse logs for {p.name}.')

            sort_key = lambda x: x.name
            self._raw_eeg_paths.sort(key=sort_key)
            self._raw_gaze_paths.sort(key=sort_key)
            self._raw_keyb_paths.sort(key=sort_key)
            self._raw_mouse_paths.sort(key=sort_key)


class EventLogRaw(EventLog):
    def __init__(self, logs):
        """ An abstraction of the raw/unparsed EEG, Gaze, Key, and Mouse
            event log data contained in the given log(s).

            ASSUMES: Strict adherence to data directory format.
            
            :param logs: ([str]) A list of log names.
        """
        super().__init__(logs)

        # Load df's from log paths
        self._df_eeg = pd_from_csvs(self._raw_eeg_paths, EVENTLOG_EEG_COLS)
        self._df_gaze = pd_from_csvs(self._raw_gaze_paths, EVENTLOG_GAZE_COLS)
        self._df_keyb = pd_from_csvs(self._raw_keyb_paths, EVENTLOG_KEYB_COLS)
        self._df_mouse = pd_from_csvs(self._raw_mouse_paths, EVENTLOG_MOUSE_COLS)
        # TODO: Keyb/mouse: strip headers
