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

BTN_STYLE = 'PanelButton.TButton'
BTN_STYLE_SPACER = 'Spacer.PanelButton.TButton'
BTN_STYLE_TOGGLE = 'PanelButtonToggle.TButton'
BTN_STYLE_TOGGLE_ON = 'Depressed.PanelButtonToggle.TButton'
BTN_SPACER_TEXT = '_spacer_'


class HUDPanel(ttk.Frame):
    def __init__(self, parent_frame, hud, x, y, btn_layout):
        """ An abstraction of a HUD panel -- A HUD Panel contains buttons
            and/or panels of its own.

            :param parent_frame: (tk.ttk.Frame) Hosting frame.
            :param hud: (hud.HUD) the 
        """
        ttk.Frame.__init__(self, takefocus=0)

        self.parent = parent_frame
        self.hud = hud
        self.x = x
        self.y = y

        # Setup panel's buttons then show the panel frame
        self._init_btns(btn_layout)
        self.grid(row=0, column=0, sticky=tk.NW)
        self.parent.grid_propagate(0)

    @classmethod
    def from_json(cls, json_path, parent_frame, hud, x, y):
        with open(json_path, 'r') as f:
            btn_layout = json.load(f, object_hook=HUDButton.from_kwargs)

        return cls(parent_frame, hud, x, y, btn_layout)

    def _init_btns(self, btn_layout):
        """ Init's the panel's buttons from the given panel layout.
        """
        self._btn_row_frames = []

        for i, panel_row in enumerate(btn_layout):
            # Create the current row's frame
            self._btn_row_frames.append(ttk.Frame(self))
            parent_row_frame = self._btn_row_frames[i]
            parent_row_frame.grid(row=i, sticky=tk.NW)

            # Add each button for curr row to its frame
            for j, btn in enumerate(panel_row):
                btn_disp_width = btn.width * HUD_BTN_WIDTH

                # If btn is a spacer, create a hidden dud btn
                if btn.text == BTN_SPACER_TEXT:
                    ttk.Button(
                        parent_row_frame,
                        width=btn_disp_width,
                        style=BTN_STYLE_SPACER
                    ).grid(row=0, column=j, ipady=4, ipadx=0)
            
                # Else create a clickable btn
                else:
                    btn.obj = ttk.Button(
                        parent_row_frame,
                        style=BTN_STYLE_TOGGLE if btn.is_toggle else BTN_STYLE,
                        width=btn_disp_width,
                        text=btn.text)
                    btn.obj.grid(row=0, column=j, ipady=4, ipadx=0)
                    btn.obj.configure(command=lambda btn=btn: \
                        self.hud.handle_payload(
                            btn.obj, btn.payload, btn.payload_type))

class HUDButton(object):
    def __init__(self, obj=None, text=None, alt_text=None, width=1,
                 is_toggle=False, payload=None, payload_type=None):
        """ An abstraction of a HUD Button.
        """
        self.obj = obj
        self.text = text
        self.alt_text = alt_text
        self.width = width
        self.is_toggle = is_toggle
        self.payload = payload
        self.payload_type = payload_type

    @classmethod
    def from_kwargs(cls, kwargs):
        return cls(**kwargs)

    @property
    def alternate_text(self):
        return self.alt_text if self.alt_text else self.text
            
