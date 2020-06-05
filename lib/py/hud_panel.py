""" Button layout handlers for the on-screen display.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import tkinter as tk
from tkinter import ttk

from lib.py.app import config


_conf = config()
HUD_BTN_SIZE = _conf['HUD_BTN_SIZE']
del _conf

STYLE_KEYB_BTN = 'vKeyboard.TButton'
STYLE_KEYB_BTN_SPECIAL = 'vKeyboardSpecial.TButton'

class HUDPanel(ttk.Frame):
    def __init__(self, parent, attach, x, y, controller):
        ttk.Frame.__init__(self, takefocus=0)

        self.attach = attach
        self.parent = parent
        self.x = x
        self.y = y
        self.controller = controller

        self._mode_frames = []    # Panel mode frames

    def set_modes(self, panel_modes):
        """ Inits each panel mode from the given list.
        """
        for mode in panel_modes:
            pframe = ttk.Frame(self.parent)
            pframe.grid(row=0, column=0, sticky="nsew")
            pframe._row_frames = []

            for i in range(len(mode)):
                pframe._row_frames.append(ttk.Frame(pframe))
                pframe._row_frames[i].grid(row=i)
                pframe._row_frames[i].raw = mode[i]

            self._init_mode_btns(pframe)
            self._mode_frames.append(pframe)
        
        # Show the first mode
        self._mode_frames[0].tkraise()

    def _init_mode_btns(self, mode_frame):
        raise NotImplementedError('Child class must overide _init_mode_btns.')


class PanelAlphaNumeric(HUDPanel):
    def __init__(self, parent, attach, x, y, controller):
        super().__init__(parent, attach, x, y, controller)

        # Define panel modes w/ shape = (NUM_MODES, NUM_ROWS, NUM_KEYS_INROW)
        panel_modes = [
            [['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'Bksp'],
             ['Sym', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
             ['ABC', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'ENTER'],
             ['<<<', '[ space ]', '>>>', 'BACK']
            ],
            [['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'Bksp'],
             ['Sym', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
             ['abc', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'ENTER'],
             ['<<<', '[ space ]', '>>>', 'BACK']
            ],
            [['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'Bksp'],
             ['abc', '!', '"', '$', '%', '&', '/', '(', ')', '[', ']', '='],
             ['@', '-', '_', '?', '#', '*', '{', '}', ':', ';', 'ENTER'],
             ['<<<','+', '[ space ]', '.', ',', '>>>', 'BACK']
            ]
        ]

        # A mapping from mode transition btns to the appropriate mode's idx
        self._mode_transition_map = {'abc': 0,
                                     'ABC': 1,
                                     'Sym': 2}

        # Init each panel mode
        self.set_modes(panel_modes)
        self.pack()

    def _init_mode_btns(self, mode_frame):
        for row in mode_frame._row_frames:
            for k_idx, k in enumerate(row.raw):
                i = k_idx
                # TODO: Move keypress handlers to hud class?
                if k == 'Bksp':
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN_SPECIAL,
                                text=k,
                                width=HUD_BTN_SIZE * 2,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k == 'Sym':
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN_SPECIAL,
                                text=k,
                                width=HUD_BTN_SIZE * 1.5,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k.lower() == 'abc':
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN_SPECIAL,
                                text=k,
                                width=HUD_BTN_SIZE * 1.5,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k == 'ENTER':
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN_SPECIAL,
                                text=k,
                                width=HUD_BTN_SIZE * 2.5,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k == '[ space ]':
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN,
                                text='     ',
                                width=HUD_BTN_SIZE * 6,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                else:
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN,
                                text=k,
                                width=HUD_BTN_SIZE,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)

    def _keypress_handler(self, k):
        """ Handles keyboard key presses.
        """
        # Catch and handle mode transition keys
        transition_to = self._mode_transition_map.get(k, None)
        if transition_to is not None:
            self._mode_frames[transition_to].tkraise()

        # TODO: Catch and handle panel toggle keys

        # Debug catches
        elif k == 'ENTER':
            self.controller.set_curr_keyboard(1) 
        elif k == 'BACK':
            self.controller.btn_to_focused_win(k) 

        # All other keys get sent as keystrokes
        else:
            if self.attach:
                self.attach.insert(tk.END, k)


class PanelNumpad(HUDPanel):
    def __init__(self, parent, attach, x, y, controller):
        super().__init__(parent, attach, x, y, controller)

        # Define panel modes of shape (NUM_MODES, NUM_ROWS, NUM_KEYS_INROW)
        panel_modes = [
            [['num', '/', '*'],
             ['7', '8', '9'],
             ['4', '5', '6'],
             ['1', '2', '3'],
             ['0', '.', 'ENTER']
            ],
            [['NUM', '/', '*'],
             ['7', '^', '9'],
             ['<', '5', '>'],
             ['1', 'v', '3'],
             ['0', '.', 'ENTER']
            ]
        ]

        # A mapping from mode transition btns to the appropriate mode's idx
        self._mode_transition_map = {'NUM': 0,
                                     'num': 1}

        # Init each panel mode
        self.set_modes(panel_modes)
        self.pack()

    def _init_mode_btns(self, mode_frame):
        for row in mode_frame._row_frames:
            for k_idx, k in enumerate(row.raw):
                i = k_idx
                if k.lower() == 'num':
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN_SPECIAL,
                                text=k,
                                width=HUD_BTN_SIZE * 1.5,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k == 'ENTER':
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN_SPECIAL,
                                text=k,
                                width=HUD_BTN_SIZE,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                else:
                    ttk.Button(row,
                                style=STYLE_KEYB_BTN,
                                text=k,
                                width=HUD_BTN_SIZE,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)

    def _keypress_handler(self, k):
        """ Handles keyboard key presses.
        """
        # Catch and handle mode transition keys
        transition_to = self._mode_transition_map.get(k, None)
        if transition_to is not None:
            self._mode_frames[transition_to].tkraise()

        # Catch and handle panel toggle keys
        elif k == 'ENTER':
            self.controller.set_curr_keyboard(0)

        # All other keys get sent as keystrokes
        else:
            if self.attach:
                self.attach.insert(tk.END, k)