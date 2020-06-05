""" A helper class for manipulation of on-screen windows.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import multiprocessing as mp
from collections import namedtuple

import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

import Xlib
import Xlib.display

from lib.py.app import warn, info

# MP queue signals
SIGNAL_STOP = -1
SIGNAL_REQUEST_ACTIVE_WINDOW = 0
SIGNAL_REQUEST_PREV_ACTIVE_WINDOW = 1


class WinMgr(object):
    def __init__(self):
        self._disp = Xlib.display.Display()
        self._wm_name = self._disp.intern_atom('_NET_WM_NAME')
        self._active_window = self._disp.intern_atom('_NET_ACTIVE_WINDOW')
        self._root = self._disp.screen().root
        self._root.change_attributes(event_mask=Xlib.X.FocusChangeMask)
        self._async_proc = None

    def _async_winstate_watcher(self, signal_queue, output_queue):
        """ The asynchronous window state watcher... It is inteded to be used 
            in a push-pull manner to send keystrokes from the 
        """
        # TODO: Move into hud as HudWinMgr
        active_window = None
        prev_active_window = None
        
        while True:
            # Watch for window state changes to track the curr/prev focus
            # TODO: Is name change watch needed?
            try:
                # TODO: Refactor some lines to init
                window_id = self._root.get_full_property(self._active_window, Xlib.X.AnyPropertyType).value[0]
                window = self._disp.create_resource_object('window', window_id)
                window.change_attributes(event_mask=Xlib.X.PropertyChangeMask)
                window_name = window.get_full_property(self._wm_name, 0).value
            except Xlib.error.XError:
                window_name = None
            
            # Denote currently/previously active windows
            if not window_name:
                pass
            elif not active_window:
                active_window = window_name
            elif window_name != active_window:
                prev_active_window = active_window
                active_window = window_name

            # Check the signal queue for signals to process. It is assumed
            # that, for a signal other than STOP to be enqued, a tracked 
            # X event has occured and is ready to be read via next_event()
            try:
                signal = signal_queue.get_nowait()
            except mp.queues.Empty:
                pass  # No news is good news
            else:
                # Process stop signal, iff received
                if signal == SIGNAL_STOP:
                    break

                # Process any "get" requests received (note above assumption)
                self._disp.next_event()

                if signal == SIGNAL_REQUEST_ACTIVE_WINDOW:
                    output_queue.put_nowait(active_window)

                elif signal == SIGNAL_REQUEST_PREV_ACTIVE_WINDOW:
                    output_queue.put_nowait(prev_active_window)
            

    def start_statewatcher(self) -> mp.Process:
        """ Starts the async window-focus watcher.
        """
        # If async watcher already running
        if self._async_proc is not None and self._async_proc.is_alive():
            warn('Win State Watcher already running.')

        # Else, not running -- start it
        else:
            ctx = mp.get_context('fork')
            self._async_signal_q = ctx.Queue(maxsize=1)
            self._async_output_q = ctx.Queue(maxsize=1)
            self._async_proc = ctx.Process(
                target=self._async_winstate_watcher, 
                args=(
                    self._async_signal_q, self._async_output_q))
            self._async_proc.start()

        return self._async_proc

    def stop_statewatcher(self) -> None:
        """ Sends the kill signal to the async watcher.
        """
        try:
            self._async_signal_q.put_nowait(SIGNAL_STOP)
        except AttributeError:
            warn('Received STOP but Win State Watcher not yet started.')
        except mp.queues.Full:
            pass

    def set_sticky_byname(self, name):
        """ Applies the sticky attribute to the window having the given name.
            If more than one window having that name is found, the attribute
            is applied to only the top-most window of that name.
        """
        # Use wnck to get the window by name and apply the attribute
        screen = Wnck.Screen.get_default()
        screen.force_update()

        ws = [w for w in screen.get_windows() if w.get_name() == name]
        ws[0].stick() if ws else None

    @property
    def active_window(self):
        """ Returns a handle to the currently active/focused window.
        """
        # Request prev active window from async queue
        try:
            self._async_signal_q.put_nowait(SIGNAL_REQUEST_ACTIVE_WINDOW)
        except AttributeError:
            warn('Requested win state but Win State Watcher not yet started.')

        # Receive state from asyc queue and return it
        return self._async_output_q.get()

    @property
    def prev_active_window(self):
        """ Returns a handle to the previously active/focused window.
        """
        # Request prev active window from async queue
        try:
            self._async_signal_q.put_nowait(SIGNAL_REQUEST_PREV_ACTIVE_WINDOW)
        except AttributeError:
            warn('Requested win state but Win State Watcher not yet started.')

        # Receive state from asyc queue and return it
        return self._async_output_q.get()