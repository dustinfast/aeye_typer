#! /usr/bin/env python
""" A module for building a HUD panel layout via keyboard strokes.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

from pynput import keyboard

from lib.py.app import config
from lib.py.hud_panel import HUDButton, HUDPayload


_conf = config()
HUD_BTN_SIZE = _conf['HUD_BTN_SIZE']
del _conf


if __name__ == '__main__':
    # Welcome msg
    print('Press the desired keys from left to right, top to bottom. To ' +
          'start a new row, press ESC. To exit, press ESC twice.\n')
    print('If a toggle key is pressed (e.g. capslock), press it twice if ' +
          'the toggle is not a desired effect.\n')

    # Setup btn-mapping
    btn_map = []
    curr_row = []
    last_pressed = None

    def on_press(key):
        global curr_row, btn_map, last_pressed

        twice_pressed = True if key == last_pressed else False
        last_pressed = key

        # Check for break/exit signals (ESC)
        if key == keyboard.Key.esc:
            # Break the current row
            btn_map.append(curr_row)
            curr_row = []

            if twice_pressed:
                return False
            
            return True

        # Convert the Key obj to its ascii value
        try:
            key_id = ord(key.char.lower())
        
        # OR, convert the Key object to it's x11 code
        except AttributeError:
            try:
                key_id = key.value.vk
            except AttributeError:
                key_id = key.vk

        if not twice_pressed:
            p = HUDPayload(key_id)
            curr_row.append(HUDButton(str(key), None, payload=p))

        print(f'Read press: {key}')

    # Map buttons from keystrokes until ESC pressed
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    # debug
    for i, row in enumerate(btn_map):
        print('Row: {i}')
        for btn in row:
            print(f'\t{btn.payload}')

    # TODO: Write to json