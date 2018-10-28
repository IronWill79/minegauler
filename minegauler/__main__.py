"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys
from os.path import join
from functools import partial
import logging
logging.basicConfig(level=logging.DEBUG)

from .shared import (files_dir, GameCellMode, GameOptionsStruct,
    GUIOptionsStruct, PersistSettingsStruct, read_settings, save_settings)
from .core import cb_core, Controller
from .gui import app, MinegaulerGUI


__version__ = '3.0.0a'

logger = logging.getLogger()

logger.info("Running...")


# Get the settings to use on startup.
settings = {}
try:
    settings = read_settings()
    logger.info("Settings read from file: %s", settings)
except FileNotFoundError:
    logger.info("Settings file not found, will use defaults")
except:
    logger.info("Unable to decode settings from file, will use defaults")

game_opts = GameOptionsStruct(
       **{k: v for k, v in settings.items() if k in GameOptionsStruct.elements})
gui_opts  = GUIOptionsStruct(
       **{k: v for k, v in settings.items() if k in GUIOptionsStruct.elements})

# Create controller.                           
ctrlr = Controller(game_opts)

# Set up GUI.
main_window = MinegaulerGUI(ctrlr.board, gui_opts)
main_window.show()
cb_core.new_game.emit()

# Connect callback for saving settings on exit.
def save_settings_cb():
    """Get the settings in use across the app and save to a file."""
    settings = PersistSettingsStruct()
    for k, v in ctrlr.opts.items():
        if k in settings.elements:
            settings[k] = v
    for k, v in main_window.opts.items():
        if k in settings.elements:
            settings[k] = v
    save_settings(settings)
                    
cb_core.save_settings.connect(save_settings_cb)

# Start the app.
sys.exit(app.exec_())
