from __future__ import print_function, unicode_literals

import logging
import os

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# dirs
DATA_DIR = 'data/bot/'


class BadWordException(Exception):
    pass


class RepetitionException(Exception):
    pass


def read(name):
    with open(os.getcwd() + '/' + name) as f:
        return [entry.rstrip('\n') for entry in f.readlines()]
