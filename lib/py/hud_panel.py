""" Button layout handlers for the on-screen display.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import json

import tkinter as tk
from tkinter import ttk

from lib.py.app import config


_conf = config()
HUD_BTN_WIDTH = _conf['HUD_BTN_WIDTH']
del _conf

BTN_STYLE = 'vKeyboard.TButton'
BTN_STYLE_STICKY = 'vKeyboardSpecial.TButton'


class HUDPanel(ttk.Frame):
    def __init__(self, parent_frame, controller, x, y, btn_layout):
        ttk.Frame.__init__(self, takefocus=0)

        self.parent = parent_frame
        self.controller = controller
        self.x = x
        self.y = y

        self._host_frame = ttk.Frame(self.parent)
        self._host_frame.grid(row=0, column=0, sticky="nsew")
        self._btn_row_frames = []

        self._init_btns(btn_layout)

        # Show the panel frame
        self._host_frame.tkraise()
        self.pack()

    @classmethod
    def from_json(cls, json_path, parent_frame, controller, x, y):
        with open(json_path, 'r') as f:
            btn_layout = json.load(f, object_hook=HUDButton.from_kwargs)

        return cls(parent_frame, controller, x, y, btn_layout)

    def _init_btns(self, btn_layout):
        """ Init's the panel's buttons from the given panel layout.
        """
        for i, panel_row in enumerate(btn_layout):
            # Create the current row's frame
            self._btn_row_frames.append(ttk.Frame(self._host_frame))
            self._btn_row_frames[i].grid(row=i)

            # Add each button for curr row to its frame
            for j, btn in enumerate(panel_row):
                p = btn.payload
                ttk.Button(
                    self._btn_row_frames[i],
                    style=BTN_STYLE_STICKY if btn.is_sticky else BTN_STYLE,
                    text=btn.text,
                    width=btn.width,
                    command=lambda btn=btn: \
                        self.controller._winmgr.payload_to_active_win(
                            btn.payload, btn.payload_type)
                ).grid(row=0, column=j)





class HUDButton(object):
    def __init__(self, text, cmd=None, width=1,
                 is_sticky=False, payload=None, payload_type=None):
        """ An abstraction of a HUD Button.
        """
        self.text = text
        self.cmd = cmd
        self.width = HUD_BTN_WIDTH * width
        self.is_sticky = is_sticky
        self.payload = payload
        self.payload_type = payload_type, 

    @classmethod
    def from_kwargs(cls, kwargs):
        return cls(**kwargs)




class PanelAlphaNumeric(HUDPanel):
    def __init__(self, parent, attach, x, y, controller):
        super().__init__(parent, attach, x, y, controller)

    def _init_mode_btns(self, mode_frame):

        for row in mode_frame._row_frames:
            for k_idx, k in enumerate(row.raw):
                i = k_idx
                if k == 'Bksp':
                    ttk.Button(row,
                                style=BTN_STYLE_STICKY,
                                text=k,
                                width=HUD_BTN_SIZE * 2,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k == 'Sym':
                    ttk.Button(row,
                                style=BTN_STYLE_STICKY,
                                text=k,
                                width=HUD_BTN_SIZE * 1.5,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k.lower() == 'abc':
                    ttk.Button(row,
                                style=BTN_STYLE_STICKY,
                                text=k,
                                width=HUD_BTN_SIZE * 1.5,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k == 'ENTER':
                    ttk.Button(row,
                                style=BTN_STYLE_STICKY,
                                text=k,
                                width=HUD_BTN_SIZE * 2.5,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                elif k == '[ space ]':
                    ttk.Button(row,
                                style=BTN_STYLE,
                                text='     ',
                                width=HUD_BTN_SIZE * 6,
                                command=lambda k=k: self._keypress_handler(k)).grid(row=0, column=i)
                else:
                    ttk.Button(row,
                                style=BTN_STYLE,
                                text=k,
                                width=HUD_BTN_SIZE,
                                command=lambda k=k: self.controller.payload_to_win(k)
                              ).grid(row=0, column=i)
