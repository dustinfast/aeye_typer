""" The on-screen heads-up display (HUD) machine learning modules. 
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import os
import pickle
from time import sleep
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import normalize
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
DATA_GROUP_KEY = 'y_key_id'                  
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

        self._gazepoint = EyeTrackerGaze()
        self._logpath = self.logfile_path
        self._modelpath = self.modelfile_path

        # Determine handler to use, based on the given mode
        self.event_handler = {
            'collect'   : self.on_event_collect,
            'train'     : self.on_event_train,
            'infer'     : self.on_event_infer
        }.get(mode, None)

        if not self.event_handler:
            raise ValueError(f'Unsupported mode: {mode}')

    @property
    def logfile_path(self):
        """ Sets up and returns the log file path.
        """
        logdir =  Path(LOG_RAW_ROOTDIR, LOG_HUD_SUBDIR)
        if not logdir.exists():
            os.makedirs(logdir)

        return str(Path(logdir, f'{DATA_SESSION_NAME}.csv'))

    @property
    def modelfile_path(self):
        """ Sets up and returns the ml model's file path.
        """
        logdir =  Path(LOG_RAW_ROOTDIR, LOG_HUD_SUBDIR)
        if not logdir.exists():
            os.makedirs(logdir)

        return str(Path(logdir, f'{DATA_SESSION_NAME}.pkl'))

    def start(self):
        """ Starts the async handlers. Returns ref to the async process.
        """
        self._gazepoint.open()
        self._gazepoint.start()
        sleep(1)  # Give the threads time to spin up
        
    def stop(self):
        """ Stops the async handlers. Returns ref to the async process.
        """
        self._gazepoint.stop()
        self._gazepoint.close()
        sleep(1)  # Give the threads time to spin down
        
    def on_event_collect(self, btn, payload=None, payload_type=None):
        """ Training data collection handler.
            
            Training data is collected as the user clicks on a btn with the
            mouse. It is assumed that on click, the user's gaze is centered
            on the on-screen keyboard button.
            # TODO: eyetracking samples are recorded leading up to each click...
        """
        # Get the centroid of the button, then write all gaze points between
        # the previous buttnon click and this one to csv
        centr_x, centr_y = btn.centroid
        
        self._gazepoint.to_csv(
            self._logpath, label=f'{centr_x}, {centr_y}, {btn.payload}')

    def on_event_train(self, btn, payload=None, payload_type=None):
        """ Training handler.
        """
        # Read in data
        df = pd.read_csv(self._logpath, 
                         header=0,
                         usecols=DATA_COL_IDXS,
                         index_col=False,
                         names=DATA_COL_NAMES)

        # TODO: Filter rows for only the last label in a series of same label
        # TODO: Possibly use second-to-last, etc, in case of eye-flirt early?
        # Possibly compress the last x samples, in case training samples have
        # longer gaze at each btn.
        # print(len(df.index))
        # df = df.drop([i for i in [i for i in df.index if df[i-1] == df[i])
        # # print(len(df.index))
        # return
        
        # _X = df[[c for c in df.columns if c.startswith('X_')]].values
        # _X[:, -2:] = normalize(_X[:, -2:])  # Leftmost 2 features get normed

        # # y -> [gazepoint_x_coord, gazepoint_y_coord]
        # _y = df[[c for c in df.columns if c.startswith('y_')]].values[:, :-1]
        # _k = df[[c for c in df.columns if c.startswith('y_')]
        #     ].values[:, -1:].squeeze()

        # print(f'\nX:\n{_X[-5:, :-2]}')
        # print(f'y:\n{_y[-5:, :]}')
        # print(f'k:\n{_k[-5:]}')
        # print(f'idx 58: {_k[58]}')
        # print(f'idx 59: {_k[59]}')
        # print(f'idx 60: {_k[60]}\n')

        
        # TODO: Do traintest split
        # X_train, X_test, y_train, y_test = train_test_split(
        #     X, y, train_size=0.8, random_state=RAND_SEED)

        # TODO: TypeR train
        # X = df[[c for c in df.columns if c.startswith('X_')]].values
        # y = df[[c for c in df.columns if c.startswith('y_')]].values
        # X[:, -2:] = normalize(X[:, -2:])  # Leftmost 2 features need normed

        # TODO: Save model to file
        # with open(self._modelpath, 'wb') as f:
        #     pickle.dump(clf, f)
        
        import matplotlib.pyplot as plt

        # MultioutputRegressor
        title = 'mro_ridge'
        X, y  = _X, _y
        from sklearn.linear_model import Ridge
        from sklearn.multioutput import MultiOutputRegressor
        clf = MultiOutputRegressor(
            Ridge(alpha=.5, random_state=RAND_SEED)).fit(X, y)
        y_hat = clf.predict(X)

        print('\nMRO Result:')
        print(f'X:\n{X[-5:, :-2]}')
        print(f'y:\n{y[-5:, :]}')
        print(f'y_hat:\n{y_hat[-5:, :]}\n')
        print('Score: %.2f' % clf.score(X, y))

        plt.figure()
        plt.scatter(y[:, 0], y[:, 1], c="green", label="y", marker=".")
        plt.scatter(y_hat[:, 0], y_hat[:, 1], c="red", marker=".",
            label="y_pred (score=%.2f)" % clf.score(X, y))
        plt.xlim([1500, 3840])
        plt.ylim([2160, 1500])
        plt.xlabel("gaze_x")
        plt.ylabel("gaze_y")
        plt.title("Perf")
        plt.legend()
        plt.savefig(f'test_{title}.png')


        # SVR
        title = 'SVR'
        X, y_x_coord, y_y_coord = (_X, _y[:, 0].squeeze(), _y[:, 1].squeeze())
        print(f'X:\n{X[-5:, :-2]}')
        print(f'y_x:\n{y_x_coord[-5:]}')
        print(f'y_y:\n{y_y_coord[-5:]}')
        from sklearn.svm import SVR

        kernel_label = ['RBF', 'Linear', 'Polynomial']
        svrs = [SVR(kernel='rbf', C=100, gamma=0.1, epsilon=.1),
                SVR(kernel='linear', C=100, gamma='auto'),
                SVR(kernel='poly', C=100, gamma='auto', degree=3, epsilon=.1,
                    coef0=1)]

        for ix, svr in enumerate(svrs):
            svr_x = svr.fit(X, y_x_coord)
            y_x_coord_hat = svr_x.predict(X)
            print(f'y_x_coord_hat:\n{y_x_coord_hat[-5:]}\n')
            
            svr_y = svr.fit(X, y_y_coord)
            y_y_coord_hat = svr_y.predict(X)
            print(f'y_y_coord_hat:\n{y_x_coord_hat[-5:]}\n')

            plt.figure()
            plt.scatter(y_x_coord, y_y_coord, c="green", label="y", marker=".")
            plt.scatter(y_x_coord_hat, y_y_coord_hat, c="red", marker=".",
                label='y_hat (score=%.2f|%.2f)' % (
                    svr_x.score(X, y_x_coord), svr_y.score(X, y_y_coord)))
            plt.xlim([1500, 3840])
            plt.ylim([2160, 1500])
            plt.xlabel("gaze_x")
            plt.ylabel("gaze_y")
            plt.title("Perf")
            plt.legend()
            plt.savefig(f'test_{title}_{kernel_label[ix]}.png')

        

        
        

    def on_event_infer(self, btn, payload=None, payload_type=None):
        pass


class _HUDInfer(object):
    def __init__(self, hud_learn):
        """ Training handler.
            
            Training occurs for two seperate models:
                1. Gaze-accuracy improvement
                2. Gaze-to-text typing
        """
        raise NotImplementedError
