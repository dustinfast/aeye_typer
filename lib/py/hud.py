""" The on-screen heads-up display (HUD). 
    A HUD contains "panels", and each panel has some number of buttons on it.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'


import multiprocessing as mp
from collections import namedtuple
from subprocess import Popen, PIPE

import Xlib.threaded
import Xlib.display
import tkinter as tk
from tkinter import ttk, FLAT, DISABLED, SUNKEN, ACTIVE
from pynput import keyboard, mouse

import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

from lib.py.app import config, warn
from lib.py.hud_panel import HUDPanel


_conf = config()
DISP_WIDTH = _conf['DISP_WIDTH_PX']
DISP_HEIGHT = _conf['DISP_HEIGHT_PX']
HUD_DISP_WIDTH = _conf['HUD_DISP_WIDTH_PX']
HUD_DISP_HEIGHT = _conf['HUD_DISP_HEIGHT_PX']
HUD_DISP_DIV = _conf['HUD_DISP_COORD_DIVISOR']
HUD_DISP_TITLE = _conf['HUD_DISP_TITLE']
DEFAULT_PANELS =  _conf['HUD_PANELS']
del _conf


BTN_FONT = ("Helvetica", 10)
BTN_FONT_BOLD = ("Helvetica", 10, "bold")

BTN_STYLE = 'PanelButton.TButton'
BTN_STYLE_SPACER = 'Spacer.PanelButton.TButton'
BTN_STYLE_TOGGLE = 'PanelButtonToggle.TButton'
BTN_STYLE_TOGGLE_ON = 'Depressed.PanelButtonToggle.TButton'


class HUD(tk.Tk):
    def __init__(self, hud_panels=DEFAULT_PANELS, sticky=True, top_level=True):
        """ An abstraction of the main heads-up display.

            :param sticky: (bool) Denotes HUD persistence across workspaces.
            :param top_level: (bool) Denotes HUD always the top-level window.
        """
        super().__init__()

        self._panel = None              # Active panel's frame
        self._panel_paths = hud_panels  # Path to each panel's layout file
        self._sticky = sticky           # Denotes HUD window stays on top

        # Calculate HUD display coords, based on screen size
        x = (DISP_WIDTH/HUD_DISP_DIV) - (HUD_DISP_WIDTH/HUD_DISP_DIV)
        y = (DISP_HEIGHT/HUD_DISP_DIV) - (HUD_DISP_HEIGHT/HUD_DISP_DIV)

        # Set HUD title/height/width/coords as well as top-window persistence
        self.winfo_toplevel().title(HUD_DISP_TITLE)
        self.geometry('%dx%d+%d+%d' % (HUD_DISP_WIDTH, HUD_DISP_HEIGHT, x, y))
        self.attributes('-topmost', 'true') if top_level else None

        # Register styles
        ttk.Style().configure(BTN_STYLE, font=BTN_FONT)
        ttk.Style().configure(BTN_STYLE_SPACER, relief=FLAT, state=DISABLED)
        ttk.Style().configure(BTN_STYLE_TOGGLE, font=BTN_FONT_BOLD)
        ttk.Style().configure(BTN_STYLE_TOGGLE_ON,
                              font=BTN_FONT_BOLD,
                              foreground='green',
                              relief=SUNKEN)

        # TODO: Add panel toggle btns -> self.set_curr_panel(idx)

        # Setup the child frame that will host the panel frames
        self._host_frame = ttk.Frame(
            self, width=HUD_DISP_WIDTH, height=HUD_DISP_HEIGHT)

        # Show 0th panel
        self.set_curr_panel(0)

        # Setup the wintools helper
        self._state_mgr = _HUDStateManager(self)

    def start(self):
        """ Brings up the HUD display. Should be used instead of tk.mainloop 
            because sticky attribute must be handled first. Blocks.
        """
        # Start the window manager
        win_mgr_proc = self._state_mgr.start_statewatcher()

        # Set sticky attribute, iff specified
        if self._sticky:
            self.update_idletasks()
            self.update()
            self._state_mgr.set_hud_sticky()

        # Start the blocking main loop
        self.mainloop()

        # Stop the focus tracker
        self._state_mgr.stop_statewatcher()
        win_mgr_proc.join()

    def set_curr_panel(self, idx):
        """ Sets the currently displayed to the requested panel.
        """
        # Denote request panel's layout file
        panel_json_path = self._panel_paths[idx]
        
        # Destroy currently active panel, if any
        if self._panel:
            self._panel.destroy()

        self._panel = HUDPanel.from_json(panel_json_path,
                                         parent_frame=self._host_frame,
                                         hud=self,
                                         x=self._host_frame.winfo_rootx(),
                                         y=self._host_frame.winfo_rooty())

    def set_btn_viz_toggle(self, btn, toggle_on=False):
        """ Sets a btn as toggled on, visually.
        """
        if toggle_on:
            btn.configure(style=BTN_STYLE_TOGGLE_ON)
        else:
            btn.configure(style=BTN_STYLE_TOGGLE)

    def handle_payload(self, btn, payload=None, payload_type=None):
        """ Fires the requested action, inferred from the payload type ID.

            :param btn: (hud_panel.HUDButton)
        """
        # Infer the correct handler to call
        # TODO: Abstract the func map
        payload_type_handler = {
            'keystroke': self._state_mgr.payload_keystroke_to_active_win,
            'key_toggle': self._state_mgr.payload_keyboard_toggle_modifer,
            'run_external': self._state_mgr.payload_run_external,
            # TODO: if payload_type = 'mouseclick_hold':
            # TODO: if payload_type = 'panel_select':
        }.get(payload_type, -1)

        if not payload_type_handler:
            raise NotImplementedError(f'Payload type: {payload_type}')

        # Call the handler
        payload_type_handler(btn=btn, 
                             payload=payload,
                             payload_type=payload_type)


class _HUDStateManager(object):
    # MP queue signals
    SIGNAL_STOP = -1
    SIGNAL_REQUEST_ACTIVE_WINDOW = 0
    SIGNAL_REQUEST_PREV_ACTIVE_WINDOW = 1

    def __init__(self, parent_hud):
        """ A helper class for allowing the HUD to interact with other windows
            via Xlib.
        """
        self.hud = parent_hud

        # Init XLib root/disp
        self._disp = Xlib.display.Display()
        self._root = self._disp.screen().root
        self._root.change_attributes(event_mask=Xlib.X.FocusChangeMask)
        self._net_wm_name = self._disp.intern_atom('_NET_WM_NAME')

        # Init keyboard/mouse controllers and containers
        # TODO: Refactor into HUDKeyboardManager
        self._mouse = mouse.Controller()
        self._keyboard = keyboard.Controller()
        self._keyboard_active_modifier_btns = []
        self._keyboard_hold_modifiers = False

        # Multi-processing attributes
        self._async_proc = None
        self._async_signal_q = None
        self._async_output_q = None

    @property
    def active_window(self):
        """ Returns an Xlib.Window obj for the currently active window.
        """
        # Request currently active window ID from async queue
        try:
            self._async_signal_q.put_nowait(self.SIGNAL_REQUEST_ACTIVE_WINDOW)
        except AttributeError:
            warn('Requested win state but Win State Watcher not yet started.')

        # Receive ID from asyc queue and return its derived window obj
        window_id = self._async_output_q.get()
        return self._disp.create_resource_object('window', window_id)

    @property
    def prev_active_window(self):
        """ Returns an Xlib.Window obj for the previously active window.
        """
        # Request prev active window ID from async queue
        try:
            self._async_signal_q.put_nowait(
                self.SIGNAL_REQUEST_PREV_ACTIVE_WINDOW)
        except AttributeError:
            warn('Requested win state but Win State Watcher not yet started.')

        # Receive ID from asyc queue and return its derived window obj
        window_id = self._async_output_q.get()
        return self._disp.create_resource_object('window', window_id)

    def _async_winstate_watcher(self, signal_queue, output_queue):
        """ The asynchronous window state watcher.
        """
        # Init local XLib root/disp, for thread safety
        disp = Xlib.display.Display()
        root = disp.screen().root
        root.change_attributes(event_mask=Xlib.X.FocusChangeMask)
        net_active_window = disp.intern_atom('_NET_ACTIVE_WINDOW')

        # Window states we'll track
        active_window_id = None
        prev_active_window_id = None
        
        while True:
            # Watch for window state changes to track the curr/prev focus
            try:
                window_id = root.get_full_property(
                    net_active_window, Xlib.X.AnyPropertyType).value[0]
                window = disp.create_resource_object('window', window_id)
                window.change_attributes(event_mask=Xlib.X.PropertyChangeMask)
            # TODO: Handle X protocol Error
            except Xlib.error.XError:
                window_id = None
            
            # Denote currently/previously active windows
            if not window_id:
                pass
            elif not active_window_id:
                active_window_id = window_id
            elif window_id != active_window_id:
                prev_active_window_id = active_window_id
                active_window_id = window_id

            # Check the signal queue for any signals to process. It is assumed
            # that for a signal other than STOP to be enqued a state change
            # has occured and is ready to be read via next_event()
            try:
                signal = signal_queue.get_nowait()
            except mp.queues.Empty:
                pass  # No news is good news
            else:
                # Process stop signal, iff received
                if signal == self.SIGNAL_STOP:
                    break

                # Process any "get" requests received (note above assumption)
                disp.next_event()

                if signal == self.SIGNAL_REQUEST_ACTIVE_WINDOW:
                    output_queue.put_nowait(active_window_id)

                elif signal == self.SIGNAL_REQUEST_PREV_ACTIVE_WINDOW:
                    output_queue.put_nowait(prev_active_window_id)

    def _focus_prev_active_win(self):
        """ Sets the previously active window to be the active window.
            Intended to be used when the HUD takes focus via a HUD btn click
            and we want to return focus to the window the HUD stole focus from.
        """
        # Get prev focused window, then give it focus
        w = self.prev_active_window
        self.set_active_window(w)

    def _reset_keyb_modifers(self, toggle_btnviz=True):
        """ Resets all active keyboard modifiers, such as alt, shift, etc.,
            but NOT capslock or numlock.

            :param toggle_btnviz: (bool) Denotes active toggle button visual
            states are also reset.
        """
        # Clear all modifiers
        with self._keyboard.modifiers as modifiers:
            for m in modifiers:
                self._keyboard.release(m)

        # Toggle-off all active modifier btns and alternate btn texts 
        if toggle_btnviz:
            for b in self._keyboard_active_modifier_btns:
                self.hud.set_btn_viz_toggle(b)

            self._keyboard_active_modifier_btns = []
            self.hud._panel.set_btn_text(use_alt_text=False)

    def start_statewatcher(self) -> mp.Process:
        """ Starts the async window-focus watcher.
        """
        # If async watcher already running
        if self._async_proc is not None and self._async_proc.is_alive():
            warn('Win State Watcher already running.')

        # Else, not running -- start it
        else:
            ctx = mp.get_context('fork')
            self._async_signal_q = ctx.Queue(maxsize=1)
            self._async_output_q = ctx.Queue(maxsize=1)
            self._async_proc = ctx.Process(
                target=self._async_winstate_watcher, 
                args=(
                    self._async_signal_q, self._async_output_q))
            self._async_proc.start()

        return self._async_proc

    def stop_statewatcher(self) -> None:
        """ Stops the async state watcher and does cleanup.
        """
        # Unset any keybd modifier toggles the user may have set
        self._reset_keyb_modifers(toggle_btnviz=False)

        # Send kill signal to the asynch watcher proc
        try:
            self._async_signal_q.put_nowait(self.SIGNAL_STOP)
        except AttributeError:
            warn('Received STOP but Win State Watcher not yet started.')
        except mp.queues.Full:
            pass

    def set_hud_sticky(self):
        """ Applies the "show on all workspaces" attribute to the HUD window.
            If more than one HUD window having that name is found, the
            attribute is applied to the top-most HUD window only.
            ASSUMES: HUD window opened before this class was instantantiated.
        """
        # Use wnck to get the window by name and apply the attribute
        screen = Wnck.Screen.get_default()
        screen.force_update()

        ws = [w for w in screen.get_windows() if w.get_name() == HUD_DISP_TITLE]
        
        if ws:
            ws[0].stick()
        else:
            raise Exception(f'Set sticky failed for hud: {HUD_DISP_TITLE}')

        del screen

    def get_win_name(self, window):
        """ Returns the window name of the given window.
        """
        return window.get_full_property(self._net_wm_name, 0).value

    def set_active_window(self, window):
        """ Gives focus to the given window.
        """
        window.set_input_focus(Xlib.X.RevertToParent, Xlib.X.CurrentTime)
        window.configure(stack_mode=Xlib.X.Above)
        self._disp.sync()

    def payload_keystroke_to_active_win(self, **kwargs):
        """ Sends the given payload to the previously active (very recently
            the actually-active, but we just stole its focus by clicking a HUD
            button) window. In the process, focus is restored to that window
            and any keyboard modifiers are unset.

            :param kwargs: Arg 'payload' is expected.
        """
        self._focus_prev_active_win()

        # Extract kwarg
        payload = kwargs['payload']     # (str)

        # Convert the payload to a KeyCode obj, then do keypress
        payload = self._keyboard._KeyCode.from_vk(payload)
        self._keyboard.press(payload)
        self._keyboard.release(payload)

        # Clear any modifers (ex: alt, shift, etc.) iff not hold set
        if not self._keyboard_hold_modifiers:
            self._reset_keyb_modifers()

    def payload_keyboard_toggle_modifer(self, **kwargs):
        """ Updates the keyboard controller to reflect the given toggle key
            press. E.g. To toggle shift key on/off. In the process, focus is
            returned to the previously focused window.

            :param kwargs: Args 'btn' and 'payload' are expected.
        """
        self._focus_prev_active_win()

        # Convenience defs
        vk_capslock = 65509
        vk_numlock = 65407
        vk_scrolllock = 65300
        vk_hold_mods = 65515
        
        # Extract kwargs
        payload = kwargs['payload']     # (int) Key vk code
        sender = kwargs['btn']    # (HUDPanel.HUDButton) Payload sender

        # Ensure modifier is supported
        if payload == vk_numlock:
            raise NotImplementedError('NumLock')
        elif payload == vk_scrolllock:
            raise NotImplementedError('ScrollLock')

        # Convert payload to KeyCode and denote capslock status
        keycode = self._keyboard._KeyCode.from_vk(payload)
        
        # If payload is for capslock, handle as a single-click modifier
        if payload == vk_capslock:
            self._keyboard.press(keycode)
            self._keyboard.release(keycode)
            self.hud.set_btn_viz_toggle(
                sender, toggle_on=self._keyboard._caps_lock)

        # Else, if payload is the hold-modifer btn
        elif payload == vk_hold_mods:
            toggle_down = not self._keyboard_hold_modifiers
            self._keyboard_hold_modifiers = toggle_down
            self.hud.set_btn_viz_toggle(sender, toggle_on=toggle_down)
            self._reset_keyb_modifers() if not toggle_down else None
            
        # Else, handle press/releases modifier (ex: alt, shift, etc.)
        else:
            with self._keyboard.modifiers as modifiers:
                modifier = self._keyboard._as_modifier(keycode)

                if not modifier:
                    raise ValueError(f'Unsupported modifier: {keycode}')

                # If btn not previously in the down state, send keypress
                if modifier not in [m for m in modifiers]:
                    toggle_down = True
                    self._keyboard.press(keycode)
                    self._keyboard_active_modifier_btns.append(sender)

                # else, send key release
                else:
                    toggle_down = False
                    self._keyboard.release(keycode)
                    self._keyboard_active_modifier_btns.remove(sender)

                # Update btn state according to new toggle state
                self.hud.set_btn_viz_toggle(sender, toggle_on=toggle_down)
                if modifier == self._keyboard._Key.shift:
                    self.hud._panel.set_btn_text(use_alt_text=toggle_down)


            # TODO: Ensure graceful handle of alt + tab, etc.

    def payload_run_external(self, **kwargs):
        """ Runs the external cmd given by the payload.

            :param kwargs: Arg 'payload' is expected.
        """
        self._focus_prev_active_win()

        # Extract kwarg
        payload = kwargs['payload']     # (str) Well-formatted python list

        # Ensure cmd given as a list of the cmd and its args
        cmd = eval(payload)
        if not cmd or not isinstance(cmd, list):
            raise ValueError(f'Invalid cmd format: {payload}')

        # Run the cmd
        proc = Popen(cmd, stderr=PIPE)
        stderr = proc.communicate()[1]
        proc.wait()

        # If there were build errors, quit
        if stderr and not stderr.decode().startswith('Created symlink'):
            warn(f'Cmd "{cmd}" stderr output: \n{stderr}')
