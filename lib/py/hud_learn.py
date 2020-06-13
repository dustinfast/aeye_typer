""" The on-screen heads-up display (HUD) machine learning modules. 
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import os
from time import sleep
from pathlib import Path

import pandas as pd
from pynput import keyboard as Keyboard
from sklearn.linear_model import Ridge
from sklearn.preprocessing import normalize
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split

import pyximport; pyximport.install()  # Required for EyeTrackerGaze

from lib.py.eyetracker_gaze import EyeTrackerGaze
from lib.py.app import key_to_id, config, info, warn


# App config elements
_conf = config()
LOG_RAW_ROOTDIR = _conf['EVENTLOG_RAW_ROOTDIR']
LOG_HUD_SUBDIR = _conf['EVENTLOG_HUD_SUBDIR']
del _conf

# Training data attributes
DATA_SESSION_NAME = '2020-06-13'
DATA_COL_NAMES = ['X_eyepos_left_x', 'X_eyepos_left_y', 'X_eyepos_left_z',
                  'X_eyepos_right_x', 'X_eyepos_right_y', 'X_eyepos_right_z',
                  'X_gaze_x', 'X_gaze_y', 'y_gaze_x', 'y_gaze_y', 'y_key_id']
DATA_COL_IDXS = [3, 4, 5, 6, 7, 8, 31, 32, 33, 34, 35]
RAND_SEED = 1234


class HUDLearn(object):
    def __init__(self, hud_state, mode):
        """ An abstraction of the HUD's machine learning element for handling
                data collection, training, and inference.
                
            :param hud_state: (hud.) The HUD's state obj.
            :param mode: (str) Either 'collect', 'train', or 'infer'.
        """
        self.hud_state = hud_state

        self.gazepoint = EyeTrackerGaze()
        self._handler = None

        # Determine handler to use, based on the given mode
        handler = {
            'collect'   : _HUDDataCollect,
            'train'     : _HUDTrain,
            'infer'     : _HUDInfer
        }.get(mode, None)

        if not handler:
            raise ValueError(f'Unsupported mode: {mode}')

        self._handler = handler(self)

    @property
    def datafile_path(self):
        # Setup and denote the log file path
        logdir =  Path(LOG_RAW_ROOTDIR, LOG_HUD_SUBDIR)
        if not logdir.exists():
            os.makedirs(logdir)

        return str(Path(logdir, f'{DATA_SESSION_NAME}.csv'))

    def start(self):
        """ Starts the async handlers. Returns ref to the async process.
        """
        if self._handler.proc.is_alive():
            warn('HUDLearn received START but is already running.')
        else:
            self.gazepoint.open()
            self.gazepoint.start()
            self._handler.proc.start()
            sleep(1)  # Give the threads time to spin up
        
        return self._handler.proc

    def stop(self):
        """ Stops the async handlers. Returns ref to the async process.
        """
        if not self._handler.proc.is_alive():
            warn('HUDLearn received STOP but is not running.')
        else:
            self.gazepoint.stop()
            self.gazepoint.close()
            self._handler.proc.stop()
        
        return self._handler.proc
        

class _HUDDataCollect(object):
    def __init__(self, hud_learn):
        """ Training data collection handler.
            
            Training data is collected as the user types on a physical keyboard.
            It is assumed that on physical key-click, the user's gaze is
            centered on the corresponding on-screen keyboard button.
            # TODO: eyetracking samples are recorded leading up to each click...
        """
        self.hud_learn = hud_learn
        self._keyb_listener = Keyboard.Listener(on_press=self._on_keypress)
        self._logpath = self.hud_learn.datafile_path

    @property
    def proc(self):
        return self._keyb_listener

    def _on_keypress(self, key):
        """ The on keypress callback.
        """
        # Get the key id and centroid of the corresponding on-screen keyboard
        # button. The centroid is assumed to be user's actual gaze location.
        key_id = key_to_id(key)
        centr = self.hud_learn.hud_state.hud.active_panel.btn_frompayload(
            key_id).centroid  # (x, y)

        # Write all gaze points between the previous event and this one to csv
        self.hud_learn.gazepoint.to_csv(
            self._logpath, label=f'{centr[0]}, {centr[1]}, {key_id}')


class _HUDTrain(object):
    def __init__(self, hud_learn):
        """ Training handler. Training occurs for two seperate models:
            (1) Gaze-accuracy improvement, and (2) Gaze-to-text typing.
        """
        self.hud_learn = hud_learn

        self._logpath = self.hud_learn.datafile_path
        self._is_alive = False

    @property
    def proc(self):
        return self

    @property
    def is_alive(self):
        return lambda: self._is_alive

    @property
    def join(self):
        return lambda: True

    @property
    def dataset_df(self):
        """ Returns a new df representation of the training data.
        """
        df = pd.read_csv(self._logpath, 
                         header=0,
                         usecols=DATA_COL_IDXS,
                         index_col=False,
                         names=DATA_COL_NAMES)

        return df
        
    def start(self):
        """ Starts model training.
            ASSUMES: A well formatted datafile at the path denoted by _logpath,
            as constructed by _HUDDataCollect.
        """
        print('Training... You may continue to use the HUD during this time.')
        self._isalive = True

        self._do_acc_train()
        # self._do_typer_train()

    def stop(self):
        """ Stops model training.
        """
        self._isalive = False
        return self.join

    def _do_acc_train(self, show_results=True):
        # Extract data
        df = self.dataset_df

        X = df[[c for c in df.columns if c.startswith('X_')]].values[:, :]
        y = df[[c for c in df.columns if c.startswith('y_')]].values[:, :-1]
        X[:, -2:] = normalize(X[:, -2:])  # Leftmost 2 features need normed

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, train_size=0.8, random_state=RAND_SEED)

        clf = MultiOutputRegressor(
            Ridge(random_state=RAND_SEED)).fit(X_train, y_train)

        if not show_results:
            return

        # Plot and show validation results
        y_hat = clf.predict(X_train)
        import matplotlib.pyplot as plt
        plt.figure()
        plt.scatter(y_train[:, 0], y_train[:, 1], c="green", label="y")
        plt.scatter(y_hat[:, 0], y_hat[:, 1], c="red",
            label="y_pred (score=%.2f)" % clf.score(X_train, y_train))
        plt.xlim([1500, 3840])
        plt.ylim([2160, 1500])
        plt.xlabel("gaze_x")
        plt.ylabel("gaze_y")
        plt.title("Comparing random forests and the multi-output meta estimator")
        plt.legend()
        plt.show()
        
    def _do_typer_train(self):
        # Extract data
        df = self.dataset_df
        X = df[[c for c in df.columns if c.startswith('X_')]].values
        y = df[[c for c in df.columns if c.startswith('y_')]].values
        X[:, -2:] = normalize(X[:, -2:])  # Leftmost 2 features need normed

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, shuffle=False, random_state=RAND_SEED)
        raise NotImplementedError


class _HUDInfer(object):
    def __init__(self, hud_learn):
        """ Training handler.
            
            Training occurs for two seperate models:
                1. Gaze-accuracy improvement
                2. Gaze-to-text typing
        """
        raise NotImplementedError
