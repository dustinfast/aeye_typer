""" The on-screen heads-up display (HUD). 
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

from time import sleep
import multiprocessing as mp
from subprocess import Popen, PIPE

import Xlib.display
import Xlib.threaded
import tkinter as tk
from tkinter import ttk, FLAT, DISABLED, SUNKEN, ACTIVE
from pynput import mouse as Mouse
from pynput import keyboard as Keyboard

import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

from lib.py.app import config, warn
from lib.py.hud_panel import HUDPanel
from lib.py.hud_learn import HUDLearn


# App config elements
_conf = config()
DISP_WIDTH = _conf['DISP_WIDTH_PX']
DISP_HEIGHT = _conf['DISP_HEIGHT_PX']
HUD_DISP_WIDTH = _conf['HUD_DISP_WIDTH_PX']
HUD_DISP_HEIGHT = _conf['HUD_DISP_HEIGHT_PX']
HUD_DISP_DIV_X = _conf['HUD_DISP_COORD_DIVISOR_X']
HUD_DISP_DIV_Y = _conf['HUD_DISP_COORD_DIVISOR_Y'] 
HUD_DISP_TITLE = _conf['HUD_DISP_TITLE']
HUD_DEFAULT_PANELS =  _conf['HUD_PANELS']
del _conf

# HUD styles
HUD_STYLE = 'HUD.TFrame'
BTN_STYLE = 'PanelButton.TButton'
BTN_STYLE_SPACER = 'Spacer.PanelButton.TButton'
BTN_STYLE_TOGGLE = 'PanelButtonToggle.TButton'
BTN_STYLE_TOGGLE_ON = 'Depressed.PanelButtonToggle.TButton'
BTN_FONT_BOLD = ("Helvetica", 10, "bold")
BTN_FONT = ("Helvetica", 10)

# VKey codes, for convenience
VK_CAPSLOCK = 65509
VK_NUMLOCK = 65407
VK_SCROLLLOCK = 65300
VK_MODLOCK = 65515
VK_NEXTCLICKLOCK = 60005
VK_CLICKREQ = 65516

# Multiproccessing attribites
SIGNAL_STOP = -1
SIGNAL_REQUEST_ACTIVE_WINDOW = 0
SIGNAL_REQUEST_PREV_ACTIVE_WINDOW = 1
ASYNC_STIME = .005


class HUD(tk.Tk):
    __valid_modes = ['basic', 'collect', 'infer']

    def __init__(self, hud_panels=HUD_DEFAULT_PANELS, mode='basic'):
        """ An abstraction of the heads-up display. A HUD contains a number of
            panels, and each panel has some number of buttons on it.
            Only one panel may be visible on the hud at a time.

            :param hud_panels: (lst) The panels (as layout file paths) to use.
            :param mode: (str) Either 'basic', 'collect', or 'infer'.
        """
        assert(mode in self.__valid_modes)
        super().__init__()

        self.active_panel = None        # Active panel's frame
        self._panel_paths = hud_panels 

        # Calculate HUD display coords, based on screen size
        x = (DISP_WIDTH/HUD_DISP_DIV_X) - (HUD_DISP_WIDTH/HUD_DISP_DIV_X)
        y = (DISP_HEIGHT/HUD_DISP_DIV_Y) - (HUD_DISP_HEIGHT/HUD_DISP_DIV_Y)

        # Set HUD title/height/width/coords/top-window-persistence
        self.winfo_toplevel().title(HUD_DISP_TITLE)
        self.attributes('-type', 'splash')
        self.attributes('-topmost', 'true')
        self.geometry('%dx%d+%d+%d' % (HUD_DISP_WIDTH, HUD_DISP_HEIGHT, x, y))

        # Register styles
        ttk.Style().configure(BTN_STYLE, font=BTN_FONT)
        ttk.Style().configure(BTN_STYLE_SPACER, relief=FLAT, state=DISABLED)
        ttk.Style().configure(BTN_STYLE_TOGGLE, font=BTN_FONT_BOLD)
        ttk.Style().configure(BTN_STYLE_TOGGLE_ON,
                              font=BTN_FONT_BOLD,
                              foreground='green',
                              relief=SUNKEN)
        ttk.Style().configure(
            HUD_STYLE, background='red' if mode == 'collect' else None)

        
        # TODO: Change gaze-mark color to reflect mode, rather than bg
        # TODO: Denote currently focused window's title
        # FIXME: If hud is clicked but outside a btn, focus is captured.
        # TODO: Helper denoting last x keystrokes

        # Setup child frame for hosting the active panel frame.
        self._host_frame = ttk.Frame(
            self, width=HUD_DISP_WIDTH, height=HUD_DISP_HEIGHT)

        # Init the HUD state mgr
        self._state = _HUDState(self, mode)
        
        # Show 0th panel
        self.set_curr_panel(0)
 
    def _quit(self, **kwargs):
        """ Quits the hud window by exiting tk.mainloop.

            :param kwargs: Unused. For compatibility with payload_handler calls.
        """
        self.quit()

    def run(self):
        """ Brings up the HUD display. Should be used instead of tk.mainloop 
            because sticky attribute must be handled first. Blocks.
        """
        # Start the managers
        self._state.start()

        # Set sticky attribute so hud appears on all workspaces
        self.update_idletasks()
        self.update()
        self._state.set_hud_sticky()

        # Start the blocking main loop
        self.mainloop()

        # Stop the managers
        self._state.stop().join

    def set_curr_panel(self, idx):
        """ Sets the currently displayed to the requested panel.
        """
        # Denote request panel's layout file
        panel_json_path = self._panel_paths[idx]
        
        # Destroy currently active panel, if any
        if self.active_panel:
            self.active_panel.destroy()

        self.active_panel = HUDPanel.from_json(
            panel_json_path,
            parent_frame=self._host_frame,
            hud=self,
            x=self._host_frame.winfo_rootx(),
            y=self._host_frame.winfo_rooty())

    def set_btn_viz_toggle(self, btn, toggle_on=False):
        """ Sets a btn as toggled on, visually.
        """
        if toggle_on:
            btn.widget.configure(style=BTN_STYLE_TOGGLE_ON)
        else:
            btn.widget.configure(style=BTN_STYLE_TOGGLE)

    def payload_handler(self, btn, payload=None, payload_type=None):
        """ Calls the state mgr's payload handler, to fire the requested
            action, as inferred from the payload type.

            :param btn: (hud_panel.HUDButton)
        """
        self._state._payload_handler(btn, payload, payload_type)

class _HUDState(object):
    def __init__(self, parent_hud, mode):
        """ An abstraction of the HUD's state, including elements of its
            environment -- Faciliates interaction with external applications
            by tracking virtual keyboard states/clicks, the currently active
            window in order to handle payload delivery, and the users gaze.

            :param parent_hud: (HUD) The parent HUD obj.
            :param mode: (str) Either 'collect', 'train', or 'infer'.
        """
        self.hud = parent_hud

        # Init XLib root/disp
        self._disp = Xlib.display.Display()
        self._root = self._disp.screen().root
        self._root.change_attributes(event_mask=Xlib.X.FocusChangeMask)
        self._net_wm_name = self._disp.intern_atom('_NET_WM_NAME')

        # Init keyboard/mouse/ml controllers
        self._learn = HUDLearn(self, mode)
        self._mouse = Mouse.Controller()
        self._keyboard = Keyboard.Controller()

        # Keyboard modifer state containers
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
            self._async_signal_q.put_nowait(SIGNAL_REQUEST_ACTIVE_WINDOW)
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
            self._async_signal_q.put_nowait(SIGNAL_REQUEST_PREV_ACTIVE_WINDOW)
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
        prop_atom = disp.intern_atom('_NET_ACTIVE_WINDOW')

        # Window states we'll track
        active_window_id = None
        prev_active_window_id = None
        
        while True:
            # Watch for window state changes to track the curr/prev focus
            window_id = root.get_full_property(
                prop_atom, Xlib.X.AnyPropertyType).value[0]
            
            if window_id:
                window = disp.create_resource_object('window', window_id)
                window.change_attributes(event_mask=Xlib.X.PropertyChangeMask)
                
                # Denote the currently/previously active windows
                if not active_window_id:
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
                sleep(ASYNC_STIME)
            else:
                # Process stop signal, iff received
                if signal == SIGNAL_STOP:
                    break

                # Process any "get" requests received (note above assumption)
                disp.next_event()

                if signal == SIGNAL_REQUEST_ACTIVE_WINDOW:
                    output_queue.put_nowait(active_window_id)

                elif signal == SIGNAL_REQUEST_PREV_ACTIVE_WINDOW:
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
            self.hud.active_panel.set_btn_text(use_alt_text=False)

    def _payload_handler(self, btn, payload=None, payload_type=None):
        """ Fires the requested action, inferred from the payload type ID.

            :param btn: (hud_panel.HUDButton)
        """
        # Infer the correct handler to call
        payload_type_handler = {
            # TODO: if payload_type = 'mouse_toggle':

            # Close the HUD
            'hud_quit': self.hud._quit,

            # Send a keystroke to the active window
            'keystroke': self.payload_keystroke_to_active_win,

            # Toggle a keyboard modifier on/off (e.g.: shift, alt, etc.)
            'key_toggle': self.payload_keyboard_toggle_modifer,

            # Run an external command
            'run_external': self.payload_run_external
        }.get(payload_type, None)

        if not payload_type_handler:
            raise NotImplementedError(f'Payload type: {payload_type}')

        # Perform AI specific actions
        self._learn.handle_event(btn=btn, 
                                 payload=payload,
                                 payload_type=payload_type)

        # Call the handler
        payload_type_handler(btn=btn, 
                             payload=payload,
                             payload_type=payload_type)

    def start(self) -> mp.Process:
        """ Starts the async window-focus watcher and the ml/eyetracker module.
        """
        # If async watcher already running
        if self._async_proc is not None and self._async_proc.is_alive():
            warn('HUD State Manager already running.')

        # Else, not running -- start it
        else:
            # Start the state watcher
            ctx = mp.get_context('fork')
            self._async_signal_q = ctx.Queue(maxsize=1)
            self._async_output_q = ctx.Queue(maxsize=1)
            self._async_proc = ctx.Process(
                target=self._async_winstate_watcher, 
                args=(
                    self._async_signal_q, self._async_output_q))
            self._async_proc.start()

            # Start the ml/eyetracker modules
            self._learn.start()

        return self._async_proc

    def stop(self) -> mp.Process:
        """ Stops the async focus watcher and eyetracker, and performs cleanup.
        """
        # Unset any keybd modifier toggles the user may have set
        self._reset_keyb_modifers(toggle_btnviz=False)

        # Send kill signal to the asynch watcher proc
        try:
            self._async_signal_q.put_nowait(SIGNAL_STOP)
        except AttributeError:
            warn('Received STOP but HUD State Manager not yet started.')
        except mp.queues.Full:
            pass
        else:
            self._learn.stop()

        return self._async_proc

    def do_mouse_press(self, x, y, button=None):
        """ Performs a mouse btn press at the given on-screen cooridnates. The
            mouse cursor is moved to that location in the process.

            :param button: (pynput.mouse.Button): The mouse-button to press. If
            None, the left mouse button is assumed.
        """
        self._mouse.position = (x, y)
        self._mouse.press(Mouse.Button.left)

    def do_mouse_release(self, x, y, button=None):
        """ Performs a mouse btn release at the given on-screen coords. The
            mouse cursor is moved to that location in the process.

            :param button: (pynput.mouse.Button): The mouse-button to press. If
            None, the left mouse button is assumed.
        """
        self._mouse.position = (x, y)
        self._mouse.release(Mouse.Button.left)

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

        # Extract kwargs
        payload = kwargs['payload']     # (int) Key vk code
        sender = kwargs['btn']          # (HUDPanel.HUDButton) Payload sender
        
        # Ensure modifier is supported
        if payload == VK_NUMLOCK:
            raise NotImplementedError('NumLock')
        elif payload == VK_SCROLLLOCK:
            raise NotImplementedError('ScrollLock')

        # Convert payload to KeyCode and denote capslock status
        keycode = self._keyboard._KeyCode.from_vk(payload)
        
        # If payload is for capslock, handle as a single-click modifier
        if payload == VK_CAPSLOCK:
            self._keyboard.press(keycode)
            self._keyboard.release(keycode)
            self.hud.set_btn_viz_toggle(
                sender, toggle_on=self._keyboard._caps_lock)

        # Else, if payload is the hold-modifer btn
        elif payload == VK_MODLOCK:
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
                    try:
                        self._keyboard_active_modifier_btns.remove(sender)
                    except ValueError:
                        # Will occur if, say, l_shift set but r_shift clicked
                        warn('Attempted to unset a modifier that was not set.')
                        return
                    else:
                        self._keyboard.release(keycode)

                # Update btn state according to new toggle state
                self.hud.set_btn_viz_toggle(sender, toggle_on=toggle_down)
                if modifier == self._keyboard._Key.shift:
                    self.hud.active_panel.set_btn_text(use_alt_text=toggle_down)

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
