""" Misc application level helpers.
"""

__author__ = 'Dustin Fast <dustin.fast@outlook.com>'

import yaml
import random
import numpy as np
from functools import lru_cache

CONFIG_FILE_PATH = '/opt/app/src/_config.yaml'

ANSII_ESC_BOLD = '\033[1m'
ANSII_ESC_OK = '\033[92m'
ANSII_ESC_WARNING = '\033[38;5;214m'
ANSII_ESC_ERROR = '\033[91m'
ANSII_ESC_ENDCOLOR = '\033[0m'


# Load the application's config file or die
try:
    with open(CONFIG_FILE_PATH, 'r') as f:
            APP_CFG = yaml.load(f, Loader=yaml.FullLoader)
except FileNotFoundError:
    print(f'FATAL: Failed to open config file \'{CONFIG_FILE_PATH}\'\n')
    exit()


@lru_cache(maxsize=100)
def app_config(s):
    """ Returns the requested application config element.
    """
    try:
        return APP_CFG[s]
    except KeyError:
        print(f'FATAL: Invalid config element requested: \'{s}\'\n')
        exit()

def seed_rand(seed=None):
    """ Seeds python.random and np.random.
    """
    if seed:
        random.seed(seed)
        np.random.seed(seed)

def key_to_id(key):
    """ Returns the key ID of the given Key obj.
    """
    # Convert the Key obj to its ascii value
    try:
        key_id = ord(key.char.lower())
    
    # OR, convert the Key object to it's x11 code
    except AttributeError:
        try:
            key_id = key.value.vk
        except AttributeError:
            key_id = key.vk

    return key_id
    
def info(s, end='\n'):
    """ Prints the given string to stdout, formatted as an info str.
    """
    print(f"{ANSII_ESC_OK}INFO:{ANSII_ESC_ENDCOLOR} {s}", end=end)


def warn(s, end='\n'):
    """ Prints the given string to stdout, formatted as a warning.
    """
    print(f"{ANSII_ESC_WARNING}WARN:{ANSII_ESC_ENDCOLOR} {s}", end=end)


def error(s, end='\n'):
    """ Prints the given string to stdout, formatted as an error.
    """
    print(f"{ANSII_ESC_ERROR}ERROR:{ANSII_ESC_ENDCOLOR} {s}", end=end)


def bold(s, end='\n'):
    """ Prints the given string to stdout in bold.
    """
    print(f"{ANSII_ESC_BOLD}{s}{ANSII_ESC_ENDCOLOR}", end=end)
