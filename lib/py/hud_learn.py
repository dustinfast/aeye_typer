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

# Data file col names, w/ prefixes X_ and y_ denoting col is feature/label 
MOUSELOG_COL_NAMES = [
    'timestamp',
    'btn_id',
    'y_click_coord_x',
    'y_click_coord_y']

GAZELOG_COL_NAMES = [ 
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

    'X_left_gazeorigin_mm_x',
    'X_left_gazeorigin_mm_y',
    'X_left_gazeorigin_mm_z',
    'X_right_gazeorigin_mm_x',
    'X_right_gazeorigin_mm_y',
    'X_right_gazeorigin_mm_z',

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
    '_combined_gazepoint_y']


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


class HUDDataGazeAccAssist(HUDLearn):
    def __init__(self, verbose=False):
        """ Top-level module for gaze-accuracy assist training data collection.
            Collection occurs as the user clicks around the screen while gazing
            at the on-screen location of each click.
        """
        super().__init__(None, None)
        self._verbose = verbose

    def collect(self):
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


class HUDTrainGazeAccAssist(HUDLearn):
    def __init__(self):
        """ Module for training the gaze-accuracy assistance models from
            the data collected by HudDataCollectGazeAccAssist.
        """
        super().__init__(None, None)

    def run(self):
        self._train_gaze_acc()

    def _get_training_df(self):
        """ Returns the training data in pd.DataFrame form.
        """
        mouse_log = self._log_path('mouse')
        gaze_log = self._log_path('gaze')

        # Load log files
        df_m = pd.read_csv(mouse_log, 
                           header=None,
                           index_col=False,
                           names=MOUSELOG_COL_NAMES)

        df_g = pd.read_csv(gaze_log, 
                           header=None,
                           index_col=False,
                           names=GAZELOG_COL_NAMES)

        # Filter gaze rows with invalid gaze-points
        df_g = df_g[df_g['X_left_pupildiameter_mm'] != -1]
        df_g = df_g[df_g['X_right_pupildiameter_mm'] != -1]
        
        # Homogenize mouse/gaze timestamp scales and precision
        df_m['timestamp'] = df_m['timestamp'] * MOUSE_TIME_IPLIER
        df_m['timestamp'] = df_m['timestamp'].astype(int)

        df_g['timestamp'] = df_g['timestamp'] * GAZE_TIME_IPLIER
        df_g['timestamp'] = df_g['timestamp'].astype(int)

        # Join the mouse log to the gaze log by timestamp, effectively
        # labeling gaze information with the x/y coord of an actual click.
        # Note that this operation leaves some rows (from df_g) with no labels;
        # in those cases, the label columns contain NaN's.
        df = df_g.join(
            df_m.set_index('timestamp'), on='timestamp', rsuffix='_')

        return df

    def _train_gaze_acc(self, split=0.80, dist_filter=140):
        """ Gaze accuracy training handler.

            :param split: (float) train/test split ratio.
            :param dist_filter: (int) Distance metric by which unreasonable
            training data rows are filtered. This is a necessary filter to 
            account for the user failing to  always look at the cursor when
            clicking.
        """
        print('Training gaze accuracy assist...')
        
        # TODO: If model files already exist, prompt for overwrite

        # Read in training data
        df = self._get_training_df()
        
        # Drop all rows that don't have labels (i.e. click coords)
        df = df.dropna().reset_index(drop=True)

        # Drop rows w/unreasonably distant labels
        df = df[
            (
                ((df['_combined_gazepoint_x'] - df['y_click_coord_x']).abs(
                    ) < dist_filter
                ) &
                ((df['_combined_gazepoint_y'] - df['y_click_coord_y']).abs(
                    ) < dist_filter)
            )
        ]

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
        model_x = SVR(kernel='rbf', C=150, epsilon=0.05).fit(
            X_train, y_train_x_coord)
        model_y = SVR(kernel='rbf', C=150, epsilon=0.05).fit(
            X_train, y_train_y_coord)

        # Validate both models
        print('Done.\nValidating...')
        y_x_coord_hat = model_x.predict(X_test)
        y_y_coord_hat = model_y.predict(X_test)
        model_x_score = mean_absolute_error(y_test_x_coord, y_x_coord_hat)
        model_y_score = mean_absolute_error(y_test_y_coord, y_y_coord_hat)
        
        print('Done:\n\tmae_x = %.4f\n\tmae_y = %.4f' % 
            (model_x_score, model_y_score))

        # Set scaler as a member of the model instance, so it's saved with it
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
        plt.xlabel("gaze_x")
        plt.ylabel("gaze_y")
        plt.title("Perf")
        plt.legend()
        plt.savefig(f'test_SVR_acc.png')
