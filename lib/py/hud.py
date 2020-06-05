""" The on-screen heads-up display (HUD). 
    A HUD contains "panels", and each panel has some number of buttons on it.
    # TODO: A HUD contains an editor window with "send" cmd.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import tkinter as tk
from tkinter import ttk

from lib.py.app import config
from lib.py.win_mgr import WinMgr
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

HUD_PANELS = (PanelAlphaNumeric, PanelNumpad)


class HUD(tk.Tk):
    def __init__(self, sticky=True, top_level=True):
        """ An abstraction of the main heads-up display - An always on top
            button display.

            :param sticky: (bool) Denotes HUD persistence across workspaces.
            :param top_level: (bool) Denotes HUD always the top-level window.
        """
        super().__init__()

        self._panel = None              # Active cmd panel obj
        self._panel_frame = None        # Active camd panel's parent frame
        self._panels = HUD_PANELS       # Control panels
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

        # TODO: Move editor pane here
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

    def test(self):
        # Get prev focused window (because we just stole focus from it)
        w = self._winmgr.prev_active_window
        
        # Set focus to that window

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
