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
                left_pupildiameter_mm,
                right_pupildiameter_mm,
                left_eyeposition_normed_x,
                left_eyeposition_normed_y,
                left_eyeposition_normed_z,
                right_eyeposition_normed_x,
                right_eyeposition_normed_y,
                right_eyeposition_normed_z,
                left_gazeorigin_mm_x,
                left_gazeorigin_mm_y,
                left_gazeorigin_mm_z,
                right_gazeorigin_mm_x,
                right_gazeorigin_mm_y,
                right_gazeorigin_mm_z,
                left_gazepoint_normed_x,
                left_gazepoint_normed_y,
                right_gazepoint_normed_x,
                right_gazepoint_normed_y):
        """ Returns the coordinate prediction from the given gaze features.
        """
        # TODO: Pass features as a c array?
        if self._model:
            try:
                pred = self._model.predict(
                    self._scaler.transform(
                        np.array([[
                            left_pupildiameter_mm,
                            right_pupildiameter_mm,
                            left_eyeposition_normed_x,
                            left_eyeposition_normed_y,
                            left_eyeposition_normed_z,
                            right_eyeposition_normed_x,
                            right_eyeposition_normed_y,
                            right_eyeposition_normed_z,
                            left_gazeorigin_mm_x,
                            left_gazeorigin_mm_y,
                            left_gazeorigin_mm_z,
                            right_gazeorigin_mm_x,
                            right_gazeorigin_mm_y,
                            right_gazeorigin_mm_z,
                            left_gazepoint_normed_x,
                            left_gazepoint_normed_y,
                            right_gazepoint_normed_x,
                            right_gazepoint_normed_y]])))
            except Exception as e:
                error(f'Coord prediction failed with\n{repr(e)}')
                return 0
            else:
                return round(pred.item())
        else:
            return 0
