"""
main_window.py - Base GUI application implementation

April 2018, Lewis Gaul

Exports:
  BaseMainWindow
    Main window class
    
  MinegaulerGUI
    Minegauler main window class
"""

import sys
from os.path import join, dirname, basename
import logging
from glob import glob

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QFrame, QAction, QActionGroup, QMenu, QSizePolicy)

from minegauler import core
from minegauler.core import cb_core
from minegauler.shared import GUIOptionsStruct, ASSERT
from .panel_widget import PanelWidget
from .minefield_widget import MinefieldWidget
from .highscores import HighscoresWindow
from .utils import img_dir, CellImageType


logger = logging.getLogger(__name__)


def ignore_event_arg(cb):
    """Allow a callback to take in an event argument which is ignored."""
    def new_cb(event):
        cb()
    return new_cb


def get_change_style_cb(img_group, style):
    """
    Get a callback function for changing changing the button style.
    Return:
      Callback function to change the button style.
    """
    def cb(event=None):
        if img_group == CellImageType.BUTTONS:
            cb_core.change_mf_style.emit(img_group, style)
        else:
            raise ValueError("Unexpected image group name")
    return cb


class BaseMainWindow(QMainWindow):
    """
    Base class for the application implementing the general layout.
    """
    BODY_FRAME_WIDTH = 5
    
    def __init__(self, title=''):
        """
        Arguments:
          title='' (string)
            The window title.
        """
        super().__init__()
        self.setWindowTitle(title)
        self.icon = QIcon(join(img_dir, 'icon.ico'))
        self.setWindowIcon(self.icon)
        # Disable maximise button
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setup_UI()
        self.init_menubars()
        # Keep track of all subwindows that are open.
        self.open_subwindows = {}
        
    def setup_UI(self):
        """
        Set up the layout of the main window GUI.
        """
        # QMainWindow objects have a central widget to be set.
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        vlayout = QVBoxLayout(central_widget)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        # Top panel widget.
        self.panel_frame = QFrame(central_widget)
        self.panel_frame.setFrameShadow(QFrame.Sunken)
        self.panel_frame.setFrameShape(QFrame.Panel)
        self.panel_frame.setLineWidth(2)
        self.panel_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        vlayout.addWidget(self.panel_frame)
        # Main body widget config - use horizontal layout for centre alignment.
        hstretch = QHBoxLayout()
        hstretch.addStretch() #left-padding for centering
        self.body_frame = QFrame(central_widget)
        self.body_frame.setFrameShadow(QFrame.Raised)
        self.body_frame.setFrameShape(QFrame.Box)
        self.body_frame.setLineWidth(self.BODY_FRAME_WIDTH)
        self.body_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hstretch.addWidget(self.body_frame)
        hstretch.addStretch() #right-padding for centering
        vlayout.addLayout(hstretch)
        
        # Name entry bar underneath the minefield
        self.footer_frame = QFrame(central_widget)
        vlayout.addWidget(self.footer_frame)
        
    def set_panel_widget(self, panel_widget):
        """
        Set the widget to occupy the top panel.
        Arguments:
          panel_widget (QWidget)
            The widget instance to place in the top panel.
        """
        lyt = QVBoxLayout(self.panel_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(panel_widget)
        self.panel = panel_widget
        
    def set_body_widget(self, body_widget):
        """
        Set the widget to occupy the main section of the GUI.
        Arguments:
          body_widget (QWidget)
            The widget instance to place in the body.
        """
        lyt = QVBoxLayout(self.body_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(body_widget)
        self.body = body_widget
        
    def set_footer_widget(self, footer_widget):
        """
        Set the widget to occupy the lower bar of the GUI.
        Arguments:
          footer_widget (QWidget)
            The widget instance to place in the lower bar.
        """
        lyt = QVBoxLayout(self.footer_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(footer_widget)
        self.footer = footer_widget
        
    def init_menubars(self):
        """
        Initialise the menubar with 'Game', 'Options' and 'Help' menus.
        """
        self.menubar = self.menuBar() # QMainWindow has QMenuBar already
        self.game_menu = self.menubar.addMenu('Game')
        self.opts_menu = self.menubar.addMenu('Options')
        self.help_menu = self.menubar.addMenu('Help')
        
    def update_size(self):
        """Update the window size."""
        self.panel_frame.adjustSize()
        self.body_frame.adjustSize()
        self.centralWidget().adjustSize()
        self.adjustSize()
        
    def show(self):
        """Show the window."""
        super().show()
        # Pack all widgets tightly, using minimum required space.
        self.setFixedSize(0, 0)
        
    def closeEvent(self, event):
        """
        Action to be performed when the window is closed. To allow the window
        to be closed, event.accept() should be called. This is provided by the
        PyQt class.
        Arguments:
          event
            The event object to be accepted if the window is to be closed.
        """
        event.accept()
    
    
class MinegaulerGUI(BaseMainWindow):
    def __init__(self, board, opts=None):
        super().__init__('MineGauler')
        if opts:
            self.opts = opts
        else:
            self.opts = GUIOptionsStruct()
        self.populate_menubars()
        self.set_panel_widget(PanelWidget(self))
        self.set_body_widget(MinefieldWidget(self,
                                             board,
                                             self.opts.btn_size,
                                             self.opts.styles))
        cb_core.update_window_size.connect(self.update_size)
        cb_core.change_mf_style.connect(self.update_style)
        self.highscores_window = HighscoresWindow(self)
        self.highscores_window.table.name_hint = self.opts.name
        
    def populate_menubars(self):
        ## GAME MENU
        # New game action
        new_game_act = self.game_menu.addAction('New game',
                                                cb_core.new_game.emit)
        new_game_act.setShortcut('F2')
        # Replay game action
        # replay_act = self.game_menu.addAction('Replay', lambda: None)
        #                                       cb_core.replay_game.emit)
        # replay_act.setShortcut('F3')
        # Show highscores action
        hs_act = self.game_menu.addAction('Highscores', self.show_highscores)
        hs_act.setShortcut('F6')
        self.game_menu.addSeparator()
        # Difficulty radiobuttons
        diff_group = QActionGroup(self, exclusive=True)
        for diff in ['Beginner', 'Intermediate', 'Expert', 'Master']:#, 'Custom']:
            diff_act = QAction(diff, diff_group, checkable=True)
            self.game_menu.addAction(diff_act)
            diff_act.id = diff[0].lower()
            # if diff_act.id == self.procr.diff:
            #     diff_act.setChecked(True)
            diff_act.triggered.connect(
                lambda _: core.change_difficulty(diff_group.checkedAction().id))
            diff_act.setShortcut(diff[0])
        self.game_menu.addSeparator()
        # Zoom board action
        # zoom_act = self.game_menu.addAction('Zoom', lambda: None)
        # Change styles options
        styles_menu = QMenu('Styles', self)
        self.game_menu.addMenu(styles_menu)
        for img_group in [CellImageType.BUTTONS]:
            img_group_name = img_group.name.capitalize() 
            submenu = QMenu(img_group_name, self)
            styles_menu.addMenu(submenu)
            group = QActionGroup(self, exclusive=True)
            for folder in glob(join(img_dir, img_group_name, '*')):
                style = basename(folder)
                style_act = QAction(style, self, checkable=True)
                if style == self.opts.styles[img_group]:
                    style_act.setChecked(True)
                group.addAction(style_act)
                style_act.triggered.connect(
                    get_change_style_cb(img_group, style))
                submenu.addAction(style_act)
        self.game_menu.addSeparator()
        # Exit window action
        exit_act = self.game_menu.addAction('Exit', self.close)
        exit_act.setShortcut('Alt+F4')
        
        ## HELP MENU
        
    def show_highscores(self):
        self.highscores_window.show()
        
    def update_style(self, img_type, style):
        self.opts.styles[img_type] = style
        
    def closeEvent(self, event):
        cb_core.save_settings.emit()
        super().closeEvent(event)
    
                   
                   
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from minegauler.core import Board
    
    app = QApplication(sys.argv)
    main_window = MinegaulerGUI(Board(4, 4))
    main_window.show()
    sys.exit(app.exec_())