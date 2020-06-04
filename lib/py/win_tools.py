""" A module for manipulating on-screen windows.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck


class WinTools(object):
    def __init__(self):
        self._screen = Wnck.Screen.get_default()

    def get_wind_byname(self, name):
        """ Returns the Wnck.Window obj for the window having the given name,
            or None if not found. If more than one window is found, only the
            first is returned.
        """
        self._screen.force_update()
        ws = [w for w in self._screen.get_windows() if w.get_name() == name]
        if ws: return ws[0]

    def stick_by_name(self, name):
        """ Applies the sticky attribute to the window having the given name.
        """
        w = self.get_wind_byname(name)
        w.stick() if w else None

    def get_active_window(self):
        self._screen.force_update()
        return self._screen.get_active_window()

    def get_prev_active_window(self):
        self._screen.force_update()
        return self._screen.get_previously_active_window()
