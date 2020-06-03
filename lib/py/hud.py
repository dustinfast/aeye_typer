""" The on-screen heads-up display.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import tkinter as tk
from tkinter import ttk

from lib.py.app import config
from lib.py.hud_panel import PanelAlphaNumeric, PanelNumpad


_conf = config()
# TODO: use tk.Tk.winfo_screenwidth(), etc., instead from lib.app
DISP_WIDTH = _conf['DISP_WIDTH_PX']
DISP_HEIGHT = _conf['DISP_HEIGHT_PX']
HUD_DISP_WIDTH = _conf['HUD_DISP_WIDTH_PX']  # TODO: Use throughout in tuples
HUD_DISP_HEIGHT = _conf['HUD_DISP_HEIGHT_PX']
HUD_DISP_DIV = _conf['HUD_DISP_COORD_DIVISOR']
del _conf

FONT_VKEYBD = ("Helvetica", 10)
FONT_VKEYBD_SPECIAL = ("Helvetica", 10, "bold")
STYLE_KEYB_BTN = 'vKeyboard.TButton'
STYLE_KEYB_BTN_SPECIAL = 'vKeyboardSpecial.TButton'

HUD_LAYOUTS = (PanelAlphaNumeric, PanelNumpad)

class HUD(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self._kb = None                 # Active cmd panel obj
        self._kb_frame = None           # Active camd panel's parent frame
        self._cmd_panels = HUD_LAYOUTS  # Control layouts
        self._output_box = None         # Debug output frame

        # Setup the tk root frame
        self._pframe = ttk.Frame(
            self, width=HUD_DISP_WIDTH, height=HUD_DISP_HEIGHT)
        self._pframe.grid_propagate(0)
        self._pframe.pack(fill="both", expand=1)

        # Set keyboard btn styles
        ttk.Style().configure(STYLE_KEYB_BTN, font=FONT_VKEYBD)
        ttk.Style().configure(STYLE_KEYB_BTN_SPECIAL, font=FONT_VKEYBD_SPECIAL)

        # Calculate & set starting disp coords, based on screen size
        x = (DISP_WIDTH/HUD_DISP_DIV) - (HUD_DISP_WIDTH/HUD_DISP_DIV)
        y = (DISP_HEIGHT/HUD_DISP_DIV) - (HUD_DISP_HEIGHT/HUD_DISP_DIV)
        self.geometry('%dx%d+%d+%d' % (HUD_DISP_WIDTH, HUD_DISP_HEIGHT, x, y))

        # TODO: Setup keyboardToggle btns
        
        # Show 0th keyboard
        self.set_curr_keyboard(0)

    def set_curr_keyboard(self, idx):
        """ Sets the currently displayed frame.
        """
        # Denote new keyb class to use
        new_keyb = self._cmd_panels[idx]
        
        # Destroy currently active keyboard frame, if any
        # TODO: Destroy all, or top-level only recursively?
        if self._kb_frame:
            self._kb.destroy()
            self._output_box.destroy()
            self._kb_frame.destroy()

        self._kb_frame = ttk.Frame(
            self._pframe, width=HUD_DISP_WIDTH, height=HUD_DISP_HEIGHT)

        self._output_box = ttk.Entry(self._kb_frame)
        self._output_box.pack(side="top")
        self._kb_frame.pack(side="top", pady=120)

        self._kb = new_keyb(parent=self._pframe,
                            attach=self._output_box,
                            x=self._kb_frame.winfo_rootx(),
                            y=self._kb_frame.winfo_rooty(),
                            controller=self)

        self._kb_frame.tkraise()
