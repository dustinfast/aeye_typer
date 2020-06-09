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

BTN_STYLE = 'Keyboard.TButton'
BTN_STYLE_TOGGLE = 'KeyboardSpecial.TButton'
BTN_SPACER_TEXT = '_spacer_'
BTN_STYLE_SPACER = 'hidden.Keyboard.TButton'



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
                # If btn is a spacer, create a hidden dud btn
                
                if btn.text == BTN_SPACER_TEXT:

                    ttk.Button(
                        self._btn_row_frames[i],
                        width=btn.width,
                        style=BTN_STYLE_SPACER
                    ).grid(row=0, column=j)
            
                # Else create a useable btn
                else:
                    ttk.Button(
                        self._btn_row_frames[i],
                        style=BTN_STYLE_TOGGLE if btn.is_toggle else BTN_STYLE,
                        text=btn.text,
                        width=btn.width,
                        command=lambda btn=btn: \
                            self.controller.handle_payload(
                                btn.payload, btn.payload_type_id)
                    ).grid(row=0, column=j)

class HUDButton(object):
    def __init__(self, text, width=1,
                 is_toggle=False, payload=None, payload_type_id=None):
        """ An abstraction of a HUD Button.
        """
        self.text = text
        self.width = HUD_BTN_WIDTH * width
        self.is_toggle = is_toggle
        self.payload = payload
        self.payload_type_id = payload_type_id

    @classmethod
    def from_kwargs(cls, kwargs):
        return cls(**kwargs)
