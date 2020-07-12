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
    def __init__(self, parent_frame, hud, grid_col):
        """ An abstraction of a HUD panel -- A HUD Panel contains buttons
            and/or panels of its own.

            :param parent_frame: (tk.ttk.Frame) Hosting frame.
            :param hud: (hud.HUD) the 
        """
        ttk.Frame.__init__(self, takefocus=0, style=HUD_STYLE)

        self.parent = parent_frame
        self.hud = hud
        self.grid(row=0, column=grid_col, sticky=tk.NW)

    def btn_payload_handler(self, btn):
        self.hud.payload_handler(btn, btn.payload, btn.payload_type)

class HUDKeyboardPanel(HUDPanel):
    def __init__(self, parent_frame, hud, json_path, grid_col):
        """ An abstraction of a HUD panel -- A HUD Panel contains buttons
            and/or panels of its own.

            :param parent_frame: (tk.ttk.Frame) Hosting frame.
            :param hud: (hud.HUD) the 
        """
        super().__init__(parent_frame, hud, grid_col)

        self._btn_row_frames = []
        self._panel_btns = []

        # Init the panel's buttons, etc, from the given panel layout file
        with open(json_path, 'r') as f:
            btn_layout = json.load(f, object_hook=HUDPanelButton.from_kwargs)

        for i, panel_row in enumerate(btn_layout):
            # Create the current row's frame
            self._btn_row_frames.append(ttk.Frame(self))
            parent_row_frame = self._btn_row_frames[i]
            parent_row_frame.grid(row=i, sticky=tk.NW)

            # Add each button for curr row to its frame
            for j, btn in enumerate(panel_row):
                btn_disp_width = btn.width * HUD_BTN_WIDTH

                # If btn is a spacer, create a flat dud btn
                if btn.text == BTN_SPACER_TEXT:
                    btn.widget = ttk.Button(
                        parent_row_frame,
                        width=btn_disp_width,
                        style=BTN_STYLE_SPACER)
                    btn.widget.grid(row=0, column=j, ipady=4, ipadx=0)
            
                # Else create a clickable keyboard btn
                else:
                    btn.widget = ttk.Button(
                        parent_row_frame,
                        style=BTN_STYLE_TOGGLE if btn.is_toggle else BTN_STYLE,
                        width=btn_disp_width,
                        text=btn.text)
                    btn.widget.grid(row=0, column=j, ipady=4, ipadx=0)
                    btn.widget.configure(
                        command=lambda btn=btn: self.btn_payload_handler(btn))

                self._panel_btns.append(btn)

    @property
    def button_widgets(self):
        """ Returns a list of the keyboard's button widgets.
        """
        widgets = []
        for row in self._btn_row_frames:
            for btn_widg in row.winfo_children():
                widgets.append(btn_widg)

        return widgets

    def set_btn_text(self, use_alt_text=False):
        """ Sets each button on the panel to use either its alternate or
            actual display text. Intended to be used for, say, toggling
            between shifted key states when shift is pressed, etc.
            
            WARN: This function is likely not thread-safe.
        """
        for i, btn_widg in enumerate(self.button_widgets):
            # Skip spacers -- they shouldn't be updated
            if btn_widg['style'] == BTN_STYLE_SPACER:
                continue

            # Set alt text iff specified
            if use_alt_text:
                btn_widg.configure(
                    text=self._panel_btns[i].alternate_text)

            # Else set primary text
            else:
                btn_widg.configure(
                    text=self._panel_btns[i].text)


class HUDPosGuidePanel(HUDPanel):
    def __init__(self, parent_frame, hud, grid_col):
        """ An abstraction of a HUD panel -- A HUD Panel contains buttons
            and/or panels of its own.

            :param parent_frame: (tk.ttk.Frame) Hosting frame.
            :param hud: (hud.HUD) the 
        """
        super().__init__(parent_frame, hud, grid_col)

        # Create the current row's frame
        host_frame = ttk.Frame(self)
        host_frame.grid(row=0, sticky=tk.NW)

        # Create a spacer in the first row
        ttk.Button(
            host_frame,
            width=7*HUD_BTN_WIDTH,
            style=BTN_STYLE_SPACER
        ).grid(row=0, column=0)

        # Create a quit button
        btn = HUDPanelButton(text='Quit', payload = 0, payload_type='hud_quit')
        btn.widget = ttk.Button(
            host_frame,
            style=BTN_STYLE_TOGGLE if btn.is_toggle else BTN_STYLE,
            width=5*HUD_BTN_WIDTH,
            text=btn.text)
        btn.widget.grid(row=0, column=1, ipady=4, ipadx=0)
        btn.widget.configure(
            command=lambda btn=btn: self.btn_payload_handler(btn))

        # Pos guide, top left (spacer
        # ttk.Button(
        #     host_frame,
        #     style=BTN_STYLE_TOGGLE if btn.is_toggle else BTN_STYLE,
        #     width=5*HUD_BTN_WIDTH,
        #     text='').grid(row=1, column=0, columnpan=3)

        


class HUDPanelButton(object):
    # TODO: Refactor as a subclass of type ttk.Button
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

            