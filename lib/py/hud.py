""" The on-screen heads-up display (HUD). 
    A HUD contains "panels", and each panel has some number of buttons on it.
    # TODO: A HUD contains an editor window with "send" cmd.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import tkinter as tk
from tkinter import ttk

from lib.py.app import config
from lib.py.hud_panel import PanelAlphaNumeric, PanelNumpad


_conf = config()
DISP_WIDTH = _conf['DISP_WIDTH_PX']
DISP_HEIGHT = _conf['DISP_HEIGHT_PX']
HUD_DISP_WIDTH = _conf['HUD_DISP_WIDTH_PX']  # TODO: Use throughout in tuples
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
    def __init__(self):
        """ An abstraction of the main heads-up display - An always on top
            button display.
        """
        super().__init__()
        self._panel = None                 # Active cmd panel obj
        self._panel_frame = None           # Active camd panel's parent frame
        self._panels = HUD_PANELS       # Control panels
        self._editor = None             # Input editor frame
                                        # TODO: each panel has its own editor?

        # Calculate HUD disp coords, based on screen size
        x = (DISP_WIDTH/HUD_DISP_DIV) - (HUD_DISP_WIDTH/HUD_DISP_DIV)
        y = (DISP_HEIGHT/HUD_DISP_DIV) - (HUD_DISP_HEIGHT/HUD_DISP_DIV)

        # Set HUD height/width/coords, and make toplevel persistent
        self.geometry('%dx%d+%d+%d' % (HUD_DISP_WIDTH, HUD_DISP_HEIGHT, x, y))
        self.attributes('-topmost', 'true')
        self.winfo_toplevel().title(HUD_DISP_TITLE)
        
        # Register btn style/font associations
        ttk.Style().configure(STYLE_KEYB_BTN, font=FONT_VKEYBD)
        ttk.Style().configure(STYLE_KEYB_BTN_SPECIAL, font=FONT_VKEYBD_SPECIAL)

        # TODO: Move editor pane here
        # TODO: Add panel toggle btns

        # Setup the frame that will host the panel frames
        self._host_frame = ttk.Frame(
            self, width=HUD_DISP_WIDTH, height=HUD_DISP_HEIGHT)
        self._host_frame.grid_propagate(0)
        self._host_frame.pack(fill="both", expand=1)
        
        # Show 0th keyboard
        self.set_curr_keyboard(0)

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
