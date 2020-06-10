#! /usr/bin/env python
""" A utility for building a HUD panel layout file (JSON) via keyboard strokes.
    The layout produced contains buttons having default names/functionality,
    therefore the user may wish to tweak the resulting JSON.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import json
import argparse
from pathlib import Path

from pynput import keyboard

from lib.py.app import config, warn
from lib.py.hud_panel import HUDButton


OUTPUT_DIR = 'lib/json/'
OUTPUT_EXT = 'json'


def json_helper(obj):
    try:
        return obj.__dict__
    except AttributeError:
        return obj

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    arg_help_str = 'Panel name. Also used as the output file name.'
    parser.add_argument('panel_name',
                        type=str,
                        help=arg_help_str)
    args = parser.parse_args()

    # Welcome msg
    print('Press the desired keys from left to right, top to bottom. ' +
          'To start a new row, press ESC. When done, press ESC twice.\n\n' +
          'If a toggle key is pressed (ex: capslock), press it twice if ' +
          'the toggle is not a desired effect.\n')

    # Btn-mapping containers
    panel_btn_map = []
    curr_map_row = []
    last_pressed = None

    # Keypress callback
    def on_press(key):
        global curr_map_row, panel_btn_map, last_pressed

        twice_pressed = True if key == last_pressed else False
        last_pressed = key

        # Check for break/exit signals (ESC)
        if key == keyboard.Key.esc:
            # If DONE signal
            if twice_pressed:
                return False
            
            # Break the current row
            panel_btn_map.append(curr_map_row)
            curr_map_row = []
            
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
            # If the key wasn't pressed twice, note it as a panel btn
            txt = str(key).replace('Key.', '').replace("'", "")
            curr_map_row.append(
                HUDButton(obj=None,
                          text=txt,
                          alt_text=None,
                          payload=key_id,
                          payload_type='keystroke'))

        print(f'Button read: {key} <{key_id}>')

    # Map buttons from keystrokes until ESC pressed
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()  # Stop listening/mapping btns

    # Write resulting layout to json, prompting to overwrite iff exists
    outfile = Path(OUTPUT_DIR, f'{args.panel_name}.{OUTPUT_EXT}')

    if outfile.exists():
        warn(f'File already exists: {outfile}')

        if input('Overwrite [y|N]? ') !='y':
            print('Done. Results not written.')
            exit()

    with open(outfile, 'w') as f:
        json.dump(panel_btn_map, f, 
                  indent=4,
                  default=json_helper,
                  separators=(',', ': '))
    
    print(f'Done. Wrote results to {outfile}.')


