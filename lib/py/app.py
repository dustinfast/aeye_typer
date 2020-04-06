""" Misc application level helpers.
"""

__author__ = 'Dustin Fast [dustin.fast@outlook.com]'

import yaml
import random
import numpy as np


CONFIG_FILE_PATH = '/opt/app/src/_config.yaml'


# Load app config
with open(CONFIG_FILE_PATH, 'r') as f:
    _config = yaml.load(f, Loader=yaml.FullLoader)



def config():
    """ Returns the application's config as a dict.
    """
    return _config


def seed_rand(seed=None):
    """ Seeds python.random and np.random.
    """
    if seed:
        random.seed(seed)
        np.random.seed(seed)