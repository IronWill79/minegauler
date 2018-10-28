"""
utils.py

March 2018, Lewis Gaul
"""

from os.path import join
try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle
import logging

from minegauler.shared import files_dir
from .callbacks import cb_core


logger = logging.getLogger(__name__)


def change_difficulty(id):
    logger.info("Changing difficulty to '%s'", id)
    if id == 'b':
        cb_core.resize_board.emit(8, 8, 10)
    elif id == 'i':
        cb_core.resize_board.emit(16, 16, 40)
    elif id == 'e':
        cb_core.resize_board.emit(30, 16, 99)
    elif id == 'm':
        cb_core.resize_board.emit(30, 30, 200)
    elif id == 'c':
        logger.warn("Custom board size not yet implemented")
    else:
        raise ValueError("Invalid difficulty ID")
        
