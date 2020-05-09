""" Misc application level helpers.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import yaml
import random
import numpy as np


CONFIG_FILE_PATH = '/opt/app/src/_config.yaml'

ANSII_ESC_BOLD = '\033[1m'
ANSII_ESC_OK = '\033[92m'
ANSII_ESC_WARNING = '\033[93m'
ANSII_ESC_ERROR = '\033[91m'
ANSII_ESC_ENDCOLOR = '\033[0m'


def config():
    """ Returns the application's config as a dict.
    """
    # Load app config
    with open(CONFIG_FILE_PATH, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def seed_rand(seed=None):
    """ Seeds python.random and np.random.
    """
    if seed:
        random.seed(seed)
        np.random.seed(seed)


def info(s):
    """ Prints the given string to stdout, formatted as an info str.
    """
    print(f"INFO: {s}")


def info_ok(s):
    """ Prints the given string to stdout, formatted as an info/OK str.
    """
    print(f"{ANSII_ESC_OK}INFO:{ANSII_ESC_ENDCOLOR} {s}")


def warn(s):
    """ Prints the given string to stdout, formatted as a warning.
    """
    print(f"{ANSII_ESC_WARNING}WARN:{ANSII_ESC_ENDCOLOR} {s}")


def error(s):
    """ Prints the given string to stdout, formatted as an error.
    """
    print(f"{ANSII_ESC_ERROR}ERROR:{ANSII_ESC_ENDCOLOR} {s}")



def bold(s):
    """ Prints the given string to stdout in bold.
    """
    print(f"{ANSII_ESC_BOLD}{s}{ANSII_ESC_ENDCOLOR}")