""" The on-screen heads-up display (HUD). 
    A HUD contains "panels", and each panel has some number of buttons on it.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'


import multiprocessing as mp
from collections import namedtuple

import Xlib
import Xlib.display
import tkinter as tk
from tkinter import ttk

import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

from lib.py.app import config, warn
from lib.py.hud_panel import PanelAlphaNumeric, PanelNumpad


_conf = config()
DISP_WIDTH = _conf['DISP_WIDTH_PX']
DISP_HEIGHT = _conf['DISP_HEIGHT_PX']
HUD_DISP_WIDTH = _conf['HUD_DISP_WIDTH_PX']
HUD_DISP_HEIGHT = _conf['HUD_DISP_HEIGHT_PX']
HUD_DISP_DIV = _conf['HUD_DISP_COORD_DIVISOR']
HUD_DISP_TITLE = _conf['HUD_DISP_TITLE']
del _conf

FONT_VKEYBD = ("Helvetica", 10)
FONT_VKEYBD_SPECIAL = ("Helvetica", 10, "bold")
STYLE_KEYB_BTN = 'vKeyboard.TButton'
STYLE_KEYB_BTN_SPECIAL = 'vKeyboardSpecial.TButton'

DEFAULT_PANELS = (PanelAlphaNumeric, PanelNumpad)


class HUD(tk.Tk):
    def __init__(self, hud_panels=DEFAULT_PANELS, sticky=True, top_level=True):
        """ An abstraction of the main heads-up display.

            :param sticky: (bool) Denotes HUD persistence across workspaces.
            :param top_level: (bool) Denotes HUD always the top-level window.
        """
        super().__init__()

        self._panel = None              # Active cmd panel obj
        self._panel_frame = None        # Active camd panel's parent frame
        self._panels = hud_panels       # Control panels
        self._editor = None             # Input editor frame
        self._sticky = sticky

        # Calculate HUD display coords, based on screen size
        x = (DISP_WIDTH/HUD_DISP_DIV) - (HUD_DISP_WIDTH/HUD_DISP_DIV)
        y = (DISP_HEIGHT/HUD_DISP_DIV) - (HUD_DISP_HEIGHT/HUD_DISP_DIV)

        # Set HUD title/height/width/coords as well as top-window persistence
        self.winfo_toplevel().title(HUD_DISP_TITLE)
        self.geometry('%dx%d+%d+%d' % (HUD_DISP_WIDTH, HUD_DISP_HEIGHT, x, y))
        self.attributes('-topmost', 'true') if top_level else None

        # Register btn style/font associations
        ttk.Style().configure(STYLE_KEYB_BTN, font=FONT_VKEYBD)
        ttk.Style().configure(STYLE_KEYB_BTN_SPECIAL, font=FONT_VKEYBD_SPECIAL)

        # TODO: Move editor panel here
        # TODO: Add panel toggle btns

        # Setup the child frame that will host the panel frames
        self._host_frame = ttk.Frame(
            self, width=HUD_DISP_WIDTH, height=HUD_DISP_HEIGHT)
        self._host_frame.grid_propagate(0)
        self._host_frame.pack(fill="both", expand=1)
        
        # Show 0th keyboard
        self.set_curr_keyboard(0)

        # Setup the wintools helper
        self._winmgr = WinMgr()

    def start(self):
        """ Brings up the HUD display. Should be used instead of tk.mainloop 
            because sticky attribute must be handled first. Blocks.
        """
        # Start the window manager
        win_mgr_proc = self._winmgr.start_statewatcher()

        # Set sticky attribute, iff specified
        if self._sticky:
            self.update_idletasks()
            self.update()
            self._winmgr.set_sticky_byname(HUD_DISP_TITLE)

        # Start the blocking main loop
        self.mainloop()

        # Stop the focus tracker
        self._winmgr.stop_statewatcher()
        win_mgr_proc.join()

    def btn_to_focused_win(self, e):
        """ Sends the given event's payload to the focused (or previously-
            focused, since we just stole its focus by clicking a HUD button)
            window. Then restore focus to that window.
        """
        # Get prev focused window
        w = self._winmgr.prev_active_window
        
        # Set focus to that window
        print(w)

        # Send keypress

    def set_curr_keyboard(self, idx):
        """ Sets the currently displayed frame.
        """
        # Denote new keyb class to use
        new_panel = self._panels[idx]
        
        # Destroy currently active keyboard frame, if any
        # TODO: Destroy all explicitly, or is top-level only sufficient?
        # TODO: Do not destroy, just hide?
        if self._panel_frame:
            self._panel.destroy()
            self._editor.destroy()
            self._panel_frame.destroy()

        self._panel_frame = ttk.Frame(
            self._host_frame, width=HUD_DISP_WIDTH, height=HUD_DISP_HEIGHT)

        self._editor = ttk.Entry(self._panel_frame)
        self._editor.pack(side="top")
        self._panel_frame.pack(side="top", pady=120)

        self._panel = new_panel(parent=self._host_frame,
                                attach=self._editor,
                                x=self._panel_frame.winfo_rootx(),
                                y=self._panel_frame.winfo_rooty(),
                                controller=self)

        self._panel_frame.tkraise()


class WinMgr(object):
    # MP queue signals
    SIGNAL_STOP = -1
    SIGNAL_REQUEST_ACTIVE_WINDOW = 0
    SIGNAL_REQUEST_PREV_ACTIVE_WINDOW = 1

    def __init__(self):
        """ A helper class for allowing the HUD to interact with other windows.
            Some of its functionality relies on Xlib, others on Wnck.
        """
        self._disp = Xlib.display.Display()
        self._root = self._disp.screen().root
        self._root.change_attributes(event_mask=Xlib.X.FocusChangeMask)
        # self._net_wm_name = self._disp.intern_atom('_NET_WM_NAME')
        self._async_proc = None

    def _async_winstate_watcher(self, signal_queue, output_queue):
        """ The asynchronous window state watcher.
        """
        net_active_window = self._disp.intern_atom('_NET_ACTIVE_WINDOW')

        # States tracked
        active_window_id = None
        prev_active_window_id = None
        
        while True:
            # Watch for window state changes to track the curr/prev focus
            try:
                window_id = self._root.get_full_property(
                    net_active_window, Xlib.X.AnyPropertyType).value[0]
                window = self._disp.create_resource_object('window', window_id)
                window.change_attributes(event_mask=Xlib.X.PropertyChangeMask)
            except Xlib.error.XError:
                window_id = None
            
            # Denote currently/previously active windows
            if not window_id:
                pass
            elif not active_window_id:
                active_window_id = window_id
            elif window_id != active_window_id:
                prev_active_window_id = active_window_id
                active_window_id = window_id

            # Check the signal queue for signals to process. It is assumed
            # that, for a signal other than STOP to be enqued, a state change
            # has occured and is ready to be read via next_event()
            try:
                signal = signal_queue.get_nowait()
            except mp.queues.Empty:
                pass  # No news is good news
            else:
                # Process stop signal, iff received
                if signal == self.SIGNAL_STOP:
                    break

                # Process any "get" requests received (note above assumption)
                self._disp.next_event()

                if signal == self.SIGNAL_REQUEST_ACTIVE_WINDOW:
                    output_queue.put_nowait(active_window_id)

                elif signal == self.SIGNAL_REQUEST_PREV_ACTIVE_WINDOW:
                    output_queue.put_nowait(prev_active_window_id)

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
            self._async_signal_q.put_nowait(self.SIGNAL_STOP)
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
        # Request currently active window ID from async queue
        try:
            self._async_signal_q.put_nowait(self.SIGNAL_REQUEST_ACTIVE_WINDOW)
        except AttributeError:
            warn('Requested win state but Win State Watcher not yet started.')

        # Receive ID from asyc queue and return its derived window obj
        window_id = self._async_output_q.get()
        return self._disp.create_resource_object('window', window_id)

    @property
    def prev_active_window(self):
        """ Returns a handle to the previously active/focused window.
        """
        # Request prev active window ID from async queue
        try:
            self._async_signal_q.put_nowait(self.SIGNAL_REQUEST_PREV_ACTIVE_WINDOW)
        except AttributeError:
            warn('Requested win state but Win State Watcher not yet started.')

        # Receive ID from asyc queue and return its derived window obj
        window_id = self._async_output_q.get()
        return self._disp.create_resource_object('window', window_id)
