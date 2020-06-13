""" The on-screen heads-up display (HUD) machine learning modules. 
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

from time import sleep
from datetime import datetime

from pynput import keyboard as Keyboard
import pyximport; pyximport.install()

from lib.py.app import key_to_id, config, info, warn
from lib.py.event_logger import EventLog
from lib.py.eyetracker_gaze import EyeTrackerGaze


# App config elements
_conf = config()
HUD_LOG_SUBDIR = _conf['EVENTLOG_HUD_SUBDIR']
del _conf


class HUDLearn(object):
    def __init__(self, hud_state, mode):
        """ An abstraction of the HUD's machine learning element for handling
                data collection, training, and inference.
                
            :param hud_state: (hud.) The HUD's state obj.
            :param mode: (str) Either 'collect', 'train', or 'infer'.
        """
        self.hud_state = hud_state

        self._gazepoint = EyeTrackerGaze()
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

    def start(self):
        """ Starts the async handlers. Returns ref to the async process.
        """
        if self._handler.async_proc.is_alive():
            warn('HUDLearn received START but is already running.')
        else:
            self._gazepoint.open()
            self._gazepoint.start()
            self._handler.async_proc.start()
            sleep(1)  # Give the threads time to spin up
        
        return self._handler.async_proc

    def stop(self):
        """ Stops the async handlers. Returns ref to the async process.
        """
        if not self._handler.async_proc.is_alive():
            warn('Keyboard watcher received STOP but is not running.')
        else:
            self._gazepoint.stop()
            self._gazepoint.close()
            self._handler.async_proc.stop()
        
        return self._handler.async_proc
        

class _HUDDataCollect(object):
    def __init__(self, hud_learn):
        """ Training data collection handler.
            
            Training data is collected as the user types on a physical keyboard.
            It is assumed that on physical key-click, the user's gaze is
            centered on the corresponding on-screen keyboard button.

            Training data format is:
                [x_gaze, y_gaze, x_btn, y_btn, keypress_id]
        """
        self.hud_learn = hud_learn
        self._keyb_listener = Keyboard.Listener(on_press=self._on_keypress)

    @property
    def async_proc(self):
        return self._keyb_listener

    def _on_keypress(self, key):
        """ The on keypress callback.
        """
        key_id = key_to_id(key)

        # Get all gaze points between the previous event and this one
        print(self.hud_learn._gazepoint.gaze_coords())

        # Actual gaze location is assumed to be the corresponding btns centroid
        btn_xy = self.hud_learn.hud_state.hud.active_panel.btn_frompayload(
            key_id).centroid

        print(btn_xy)  # debug
        print()

        # Write to log



class _HUDTrain(object):
    def __init__(self, hud_learn):
        """ Training handler.
            
            Training occurs for two seperate models:
                1. Gaze-accuracy improvement
                2. Gaze-to-text typing
        """
        raise NotImplementedError

class _HUDInfer(object):
    def __init__(self, hud_learn):
        """ Training handler.
            
            Training occurs for two seperate models:
                1. Gaze-accuracy improvement
                2. Gaze-to-text typing
        """
        raise NotImplementedError    
