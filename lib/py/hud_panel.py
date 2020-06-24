""" Abstractions for the HUD panel and panel-button elements.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import json
from collections import OrderedDict

import tkinter as tk
from tkinter import ttk

from lib.py.app import config


_conf = config()
HUD_BTN_WIDTH = _conf['HUD_BTN_WIDTH']
del _conf

# HUD styles
HUD_STYLE = 'HUD.TFrame'
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
        ttk.Frame.__init__(self, takefocus=0, style=HUD_STYLE)

        self.parent = parent_frame
        self.hud = hud
        self.x = x
        self.y = y

        # Setup panel buttons then show the panel frame
        self.grid(row=0, column=0)
        self._init_btns(btn_layout)

    @classmethod
    def from_json(cls, json_path, parent_frame, hud, x, y):
        with open(json_path, 'r') as f:
            btn_layout = json.load(f, object_hook=HUDButton.from_kwargs)

        return cls(parent_frame, hud, x, y, btn_layout)

    def _init_btns(self, btn_layout):
        """ Init's the panel's buttons from the given panel layout.
        """
        self._btn_row_frames = []
        self._hud_btns = []
        self._payload_to_btn = {}   # { payload: HUDBtn }

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
                    btn.widget = ttk.Button(
                        parent_row_frame,
                        width=btn_disp_width,
                        style=BTN_STYLE_SPACER)
                    btn.widget.grid(row=0, column=j, ipady=4, ipadx=0)
            
                # Else create a clickable btn
                else:
                    btn.widget = ttk.Button(
                        parent_row_frame,
                        style=BTN_STYLE_TOGGLE if btn.is_toggle else BTN_STYLE,
                        width=btn_disp_width,
                        text=btn.text)
                    btn.widget.grid(row=0, column=j, ipady=4, ipadx=0)
                    btn.widget.configure(command=lambda btn=btn: \
                        self.hud.payload_handler(
                            btn, btn.payload, btn.payload_type))

                self._hud_btns.append(btn)
                self._payload_to_btn[btn.payload] = btn

    @property
    def button_widgets(self):
        """ Returns a list of the panel button widgets.
        """
        widgets = []
        for row in self._btn_row_frames:
            for btn_widg in row.winfo_children():
                widgets.append(btn_widg)

        return widgets

    def btn_frompayload(self, payload):
        """ Returns the button having the given payload. If multiple buttons
            have that payload, only the first is returned.
        """
        return self._payload_to_btn[payload]

    def set_btn_text(self, use_alt_text=False):
        """ Sets each button on the panel to use either its alternate or
            actual display text. Note that this is not thread-safe.
        """
        for i, btn_widg in enumerate(self.button_widgets):
            # Skip spacers -- they shouldn't be updated
            if btn_widg['style'] == BTN_STYLE_SPACER:
                continue

            # Set alt text iff specified
            if use_alt_text:
                btn_widg.configure(
                    text=self._hud_btns[i].alternate_text)

            # Else set primary text
            else:
                btn_widg.configure(
                    text=self._hud_btns[i].text)


class HUDButton(object):
    def __init__(self, widget=None, text=None, alt_text=None, width=1,
                 is_toggle=False, payload=None, payload_type=None):
        """ An abstraction of a HUD Button.
        """
        self.widget = widget
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

    @property
    def centroid(self):
        """ The center of the button, in on-screen coords. Result is cached
            after first call.
        """
        try:
            return self._centroid
        except AttributeError:
            obj = self.widget
            self._centroid = (
                obj.winfo_rootx() + int(obj.winfo_reqwidth() / 2),
                obj.winfo_rooty() + int(obj.winfo_reqheight() / 2))
            return self._centroid

            