""" The eyetracking gazepoint accuracy predictor.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

class EyeTrackerCoordPredict():
    def __init__(self, model_path):
        self._path = model_path
    
    def predict(self, a, b):
        return a + b
