""" The eyetracking gazepoint accuracy predictor.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import pickle


class EyeTrackerCoordPredict():
    def __init__(self, model_path):
        print('Path: ' + model_path)
        # with open(model_path, 'wb') as f:
        #     self._model = pickle.load(f)
        # pass
    
    def predict(self, 
                eyepos_left_x, 
                eyepos_left_y, 
                eyepos_left_z,
                eyepos_right_x, 
                eyepos_right_y,
                eyepos_right_z,
                gaze_coord_x, 
                gaze_coord_y):
        return gaze_coord_x
