""" The on-screen keyboard display.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import tkinter as tk
from tkinter import ttk

from lib.py.app import config
from lib.py.onscreen_layouts import KeyboardAlphaNumeric, KeyboardCmdKeys


_conf = config()
# TODO: use tk.Tk.winfo_screenwidth(), etc., instead from lib.app
DISP_WIDTH = _conf['DISP_WIDTH_PX']
DISP_HEIGHT = _conf['DISP_HEIGHT_PX']
KEYB_DISP_WIDTH = _conf['KEYB_DISP_WIDTH_PX']  # TODO: Use throughout in tuples
KEYB_DISP_HEIGHT = _conf['KEYB_DISP_HEIGHT_PX']
KEYB_DISP_DIV = _conf['KEYB_DISP_COORD_DIVISOR']
del _conf

FONT_VKEYBD = ("Helvetica", 10)
FONT_VKEYBD_SPECIAL = ("Helvetica", 10, "bold")
STYLE_KEYB_BTN = 'vKeyboard.TButton'
STYLE_KEYB_BTN_SPECIAL = 'vKeyboardSpecial.TButton'

KEYBOARDS = (KeyboardAlphaNumeric, KeyboardCmdKeys)

class OnscreenKeyboard(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self._kb = None                 # Active keyboard's parent frame
        self._kb_frame = None           # Active keyboard's parent frame
        self._keyboards = KEYBOARDS     # Keyboard layouts
        self._output_box = None         # Debug output frame

        # Setup the tk root frame
        self._pframe = ttk.Frame(
            self, width=KEYB_DISP_WIDTH, height=KEYB_DISP_HEIGHT)
        self._pframe.grid_propagate(0)
        self._pframe.pack(fill="both", expand=1)

        # Set keyboard btn styles
        ttk.Style().configure(STYLE_KEYB_BTN, font=FONT_VKEYBD)
        ttk.Style().configure(STYLE_KEYB_BTN_SPECIAL, font=FONT_VKEYBD_SPECIAL)

        # Calculate & set starting disp coords, based on screen size
        x = (DISP_WIDTH/KEYB_DISP_DIV) - (KEYB_DISP_WIDTH/KEYB_DISP_DIV)
        y = (DISP_HEIGHT/KEYB_DISP_DIV) - (KEYB_DISP_HEIGHT/KEYB_DISP_DIV)
        self.geometry('%dx%d+%d+%d' % (KEYB_DISP_WIDTH, KEYB_DISP_HEIGHT, x, y))
        
        # Show 0th keyboard
        self.set_curr_keyboard(0)

    def set_curr_keyboard(self, idx):
        """ Sets the currently displayed frame.
        """
        # Denote new keyb class to use
        new_keyb = self._keyboards[idx]
        
        # Destroy currently active keyboard frame, if any
        if self._kb_frame:
            self._kb.destroy()
            self._output_box.destroy()
            self._kb_frame.destroy()

        self._kb_frame = ttk.Frame(self._pframe, width=480, height=280)

        self._output_box = ttk.Entry(self._kb_frame)
        self._output_box.pack(side="top")
        self._kb_frame.pack(side="top", pady=125)

        self._kb = new_keyb(parent=self._pframe,
                            attach=self._output_box,
                            x=self._output_box.winfo_rootx(),
                            y=self._output_box.winfo_rooty(
                                ) + self._output_box.winfo_reqheight(),
                            controller=self)

        self._kb_frame.tkraise()
