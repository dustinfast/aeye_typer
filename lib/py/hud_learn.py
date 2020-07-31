""" The on-screen heads-up display (HUD) machine learning elements. 
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import os
import pickle
from time import sleep
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt
from sklearn.svm import SVR
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from lib.py.app import key_to_id, config, info, warn
from lib.py.event_logger import AsyncGazeEventLogger, AsyncMouseClkEventLogger


# App config elements
_conf = config()
LOG_RAW_ROOTDIR = _conf['EVENTLOG_RAW_ROOTDIR']
WRITE_BACK = _conf['EYETRACKER_WRITEBACK_SECONDS']
WRITE_AFTER = _conf['EYETRACKER_WRITEAFTER_SECONDS']
GAZE_TIME_IPLIER = _conf['GAZE_TIME_CONVERT_IPLIER']
MOUSE_TIME_IPLIER = _conf['MOUSE_TIME_CONVERT_IPLIER']
del _conf

# Training data/session attributes
DATA_SESSION_NAME = '2020-07-30'
RAND_SEED = 1234


class HUDLearn(object):
    def __init__(self, hud_state, mode):
        """ An abstraction of the HUD's machine learning element for handling
            data collection, training, and inference.
                
            :param hud_state: (hud.) The HUD's state obj.
            :param mode: (str) Either 'basic' or 'infer'.
        """
        self.hud_state = hud_state

        self._logpath = self._log_path()
        self.model_x_path = self._model_path('x')
        self.model_y_path = self._model_path('y')

        # Determine handler to use, based on the given mode
        self.handle_event = {
            'basic'     : self._null,
            'infer'     : self._null
        }.get(mode, self._null)

    def _log_path(self, suffix=None):
        """ Returns the log file path after ensuring it exists.
        """
        logdir =  Path(LOG_RAW_ROOTDIR)
        if not logdir.exists():
            os.makedirs(logdir)

        if suffix:
            return str(Path(logdir, f'{DATA_SESSION_NAME}_{suffix}.csv'))
        else:
            return str(Path(logdir, f'{DATA_SESSION_NAME}.csv'))

    def _model_path(self, suffix):
        """ Rreturns the ml model file path after ensuring it exists.
        """
        logdir =  Path(LOG_RAW_ROOTDIR)
        if not logdir.exists():
            os.makedirs(logdir)

        return str(Path(logdir, f'{DATA_SESSION_NAME}_{suffix}.pkl'))

    def _null(self, **kwargs):
        """ Dummy function, for 'basic' mode compatibility.
        """
        pass


class HUDCollect(HUDLearn):
    def __init__(self, verbose=False):
        """ Top-level data collection module for gaze-accuracy assist.
        """
        super().__init__(None, None)
        self._verbose = verbose

    def run(self):
        """ Starts data collection. Blocks until terminated.
        """
        gaze_logger = AsyncGazeEventLogger(
            self._log_path('gaze'), self._verbose)
        
        mouse_logger = AsyncMouseClkEventLogger(
            self._log_path('mouse'), [gaze_logger.event], self._verbose)

        # Start the loggers and block until terminated
        gaze_logger.start()
        log_proc = mouse_logger.start()
        log_proc.join()

        # Cleanup
        gaze_logger.stop()


class HUDTrain(HUDLearn):

    __mouse_col_names = [
        'timestamp',
        'btn_id',
        'y_x',
        'y_y'
    ]

    __gaze_col_names = [ 
        'timestamp',
        
        'X_left_pupildiameter_mm',
        'X_right_pupildiameter_mm',

        'X_left_eyeposition_normed_x',
        'X_left_eyeposition_normed_y',
        'X_left_eyeposition_normed_z',
        'X_right_eyeposition_normed_x',
        'X_right_eyeposition_normed_y',
        'X_right_eyeposition_normed_z',

        '_left_eyecenter_mm_x',
        '_left_eyecenter_mm_y',
        '_left_eyecenter_mm_z',
        '_right_eyecenter_mm_x',
        '_right_eyecenter_mm_y',
        '_right_eyecenter_mm_z',

        '_left_gazeorigin_mm_x',
        '_left_gazeorigin_mm_y',
        '_left_gazeorigin_mm_z',
        '_right_gazeorigin_mm_x',
        '_right_gazeorigin_mm_y',
        '_right_gazeorigin_mm_z',

        '_left_gazepoint_mm_x',
        '_left_gazepoint_mm_y',
        '_left_gazepoint_mm_z',
        '_right_gazepoint_mm_x',
        '_right_gazepoint_mm_y',
        '_right_gazepoint_mm_z',
        'X_left_gazepoint_normed_x',
        'X_left_gazepoint_normed_y',
        'X_right_gazepoint_normed_x',
        'X_right_gazepoint_normed_y',

        '_combined_gazepoint_x',
        '_combined_gazepoint_y'
    ]

    def __init__(self):
        """ Training handler.
            
            Training occurs for two seperate models:
                1. Gaze-accuracy improvement
                2. Gaze-to-text typing
        """
        super().__init__(None, None)

    def run(self):
        self._train_gaze_acc()

    def _get_training_df(self):
        """ Returns the training data in pd.DataFrame form.
        """
        mouse_log = self._log_path('mouse')
        gaze_log = self._log_path('gaze')
        # mouse_log = '/opt/app/data/logs/test_mouse.csv'
        # gaze_log = '/opt/app/data/logs/test_gaze.csv'

        # Load log files
        df_m = pd.read_csv(mouse_log, 
                           header=None,
                           index_col=False,
                           names=self.__mouse_col_names)

        df_g = pd.read_csv(gaze_log, 
                           header=None,
                           index_col=False,
                           names=self.__gaze_col_names)

        # Filter gaze log for no gp
        df_g = df_g[df_g['X_left_pupildiameter_mm'] != -1]
        df_g = df_g[df_g['X_right_pupildiameter_mm'] != -1]
        
        # Convert log timestamp scales
        df_m['timestamp'] = df_m['timestamp'] * MOUSE_TIME_IPLIER
        df_m['timestamp'] = df_m['timestamp'].astype(int)

        df_g['timestamp'] = df_g['timestamp'] * GAZE_TIME_IPLIER
        df_g['timestamp'] = df_g['timestamp'].astype(int)

        # Join the mouse log to the gaze log, by timestamp
        df = df_g.join(
            df_m.set_index('timestamp'), on='timestamp', rsuffix='_')

        return df
    
    def _train_gaze_acc(self, split=0.80):
        """ Gaze accuracy training handler.
        """
        print('Training...')
        
        # TODO: If model files already exist, prompt for overwrite

        # Read in training data and drop all unassociated rows
        df = self._get_training_df()
        df.dropna(inplace=True)

        # Extract X, as [[feature_1, feature_2, ...], ...]
        _X = df[[c for c in df.columns if c.startswith('X_')]].values

        # Extract y, as [[gazepoint_x_coord, gazepoint_y_coord], ... ]
        _y = df[[c for c in df.columns if c.startswith('y_')]].values

        # Do traintest split
        X_train, X_test, y_train, y_test = train_test_split(
            _X, _y, train_size=split, random_state=RAND_SEED)

        # Scale training set, then scale test set from its scaler
        scaler = MinMaxScaler()
        scaler.fit(X_train)
        X_train = scaler.transform(X_train)
        X_test = scaler.transform(X_test)
        
        # Break labels into their x/y coord components
        y_train_x_coord, y_train_y_coord = (
            y_train[:, 0].squeeze(), y_train[:, 1].squeeze())
        y_test_x_coord, y_test_y_coord = (
            y_test[:, 0].squeeze(), y_test[:, 1].squeeze())

        # Train two seperate models, one for the x coord, and one for y
        model_x = SVR(kernel='rbf', C=250, epsilon=0).fit(
            X_train, y_train_x_coord)
        model_y = SVR(kernel='rbf', C=250, epsilon=0).fit(
            X_train, y_train_y_coord)

        # Validate
        print('Validating...')
        y_x_coord_hat = model_x.predict(X_test)
        y_y_coord_hat = model_y.predict(X_test)
        model_x_score = mean_absolute_error(y_test_x_coord, y_x_coord_hat)
        model_y_score = mean_absolute_error(y_test_y_coord, y_y_coord_hat)
        
        print('Done:\n\tmae_x = %.4f\n\tmae_y = %.4f' % 
            (model_x_score, model_y_score))

        # Set scaler as a model member, so it's saved with it
        model_x.scaler = scaler
        model_y.scaler = scaler
        
        # Save models to file
        with open(self.model_x_path, 'wb') as f:
            pickle.dump(model_x, f)
        with open(self.model_y_path, 'wb') as f:
            pickle.dump(model_y, f)

        # # Plot x/y coord actual vs x/y coord pred, for testing convenience
        plt.figure()
        plt.scatter(
            y_test_x_coord, y_test_y_coord, c="green", label="x/y", marker=".")
        plt.scatter(
            y_x_coord_hat, y_y_coord_hat, c="red", marker=".",
                label='x/y pred (score=%.4f|%.4f)' % (
                    model_x_score, model_y_score))
        plt.xlim([1500, 3840])
        plt.ylim([2160, 1500])
        plt.xlabel("gaze_x")
        plt.ylabel("gaze_y")
        plt.title("Perf")
        plt.legend()
        plt.savefig(f'test_SVR_acc.png')
