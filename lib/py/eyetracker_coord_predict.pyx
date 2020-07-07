#cython: language_level=3
""" The eyetracking gazepoint accuracy predictor.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import pickle

import numpy as np

from app import error

class EyeTrackerCoordPredict():
    def __init__(self, model_path):
        """ An abstraction of a trained gaze-coord prediction model. Note that
            each instance of EyeTrackerCoordrPredict predicts only a single
            coordinate. To predict, say, coords x and y, two objs must be
            instantiated with each passed the model trained for that coord.
        """
        # Load the predictive model and feature scalar from file
        try:
            with open(model_path, 'rb') as f:
                self._model = pickle.load(f)
        except Exception as e:
            error(f'Failed to load {model_path} due to\n{repr(e)}')
            self._model = None
        else:
            self._scaler = self._model.scaler
    
    def predict(self, 
                eyepos_left_x, 
                eyepos_left_y, 
                eyepos_left_z,
                eyepos_right_x, 
                eyepos_right_y,
                eyepos_right_z,
                gaze_coord_x, 
                gaze_coord_y):
        """ Returns the coordinate prediction from the given gaze features.
        """
        # TODO: Pass features as a c array?
        if self._model:
            try:
                pred = self._model.predict(
                    self._scaler.transform(
                        np.array([[
                            eyepos_left_x, 
                            eyepos_left_y, 
                            eyepos_left_z,
                            eyepos_right_x, 
                            eyepos_right_y,
                            eyepos_right_z,
                            gaze_coord_x, 
                            gaze_coord_y]])))
            except Exception as e:
                error(f'Coord prediction failed with\n{repr(e)}')
                return 0
            else:
                return round(pred.item())
        else:
            return 0
