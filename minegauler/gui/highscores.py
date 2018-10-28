"""
highscores.py - Highscores window implementation

July 2018, Lewis Gaul
"""


import sys
import datetime as dt
import logging

from PyQt5.QtCore import (pyqtSlot, pyqtSignal, Qt, QVariant, QPoint, QRect,
    QSize, QAbstractTableModel, QAbstractItemModel)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtWidgets import (QMainWindow, QTableView, QWidget, QHBoxLayout,
    QAbstractItemView, QHeaderView, QMenu, QAction, QLineEdit, QWidgetAction,
    QActionGroup, QAbstractScrollArea)

from minegauler.shared import HighscoreSettingsStruct
from minegauler.core import cb_core
from minegauler.core.highscores import get_highscores, filter_and_sort


logger = logging.getLogger(__name__)


class HighscoresWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Highscores')
        self.table = HighscoresTable()
        self.model = HighscoresModel(self)
        self.table.setModel(self.model)
        self.setupUI()
        self.setFixedWidth(self.table.width() + 46)
        self.model.sort_changed.connect(self.table.set_sort_indicator)
        self.table.add_filter.connect(self.set_filter)
        self.set_sort_column('time')
        
    def setupUI(self):
        self.setCentralWidget(QWidget(self))
        lyt = QHBoxLayout(self.centralWidget())
        # settings_frame = QFrame(self)
        # lyt.addWidget(settings_frame) #[currently not implemented]
        # settings_frame.setLineWidth(2)
        # settings_frame.setFrameShape(QFrame.StyledPanel)
        # Make highscores table.
        lyt.addWidget(self.table)
        # Make settings/filter panel.
        # lyt = QVBoxLayout(settings_frame)
        # settings_frame.setFixedSize(200, 200)
        
    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape]:
            if self.parent():
                self.hide()
            else:
                self.close()
            # if self.gui:
            #     self.gui.open_windows.pop('highscores')
        else:
            super().keyPressEvent(event)
            
    def set_sort_column(self, sort_by):
        self.model.sort(self.model.headers.index(sort_by))
            
    @pyqtSlot(str, str)
    def set_filter(self, filter_by, filter):
        self.model.filters[filter_by] = filter
        self.model.filter_and_sort()


class HighscoresTable(QTableView):
    add_filter = pyqtSignal(str, str)
    def __init__(self):
        super().__init__()
        self.header = self.horizontalHeader()
        self.index = self.verticalHeader()
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        # self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        self.setStyleSheet("""background: rgb(215,215,255);
                              font:       normal 9pt Sans-serif;""")
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCornerButtonEnabled(False)
        self.setSortingEnabled(True)
        # Fix width of all columns, let first column stretch to width.
        self.header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.header.setSortIndicatorShown(True)
        # Sort indicator is changed by clicking a header column, although in
        #  most cases this won't change the sorting, so the indicator needs to
        #  be changed back. 
        self.header.sortIndicatorChanged.connect(
                                       lambda _1, _2: self.set_sort_indicator())
        self.header.sectionClicked.connect(self.show_header_menu)
        # Set height of rows.
        self.index.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.index.setSectionsClickable(False)
        self.sort_index = 0
        self.filter_menu = QMenu(None)
        self.block_header_menu = False
        self.name_hint = None
    
    @pyqtSlot()
    @pyqtSlot(int)
    def set_sort_indicator(self, col=None):
        """Set the sort indicator to match the actual sorting."""
        if col is not None:
            self.sort_index = col
        self.header.setSortIndicator(self.sort_index, Qt.DescendingOrder)
        
    @pyqtSlot(int)
    def show_header_menu(self, col):
        key = self.model().headers[col]
        if key not in ['name', 'flagging'] or self.block_header_menu:
            self.block_header_menu = False
            return
        self.filter_menu = QMenu(self.parent())
        self.filter_menu.aboutToHide.connect(
                                           self.check_mouse_on_header_menu_hide)
        def get_filter_cb(key, f):
            def cb():
                self.add_filter.emit(key, f)
                self.block_header_menu = False
            return cb 
            
        if key == 'flagging':                
            group = QActionGroup(self, exclusive=True)
            for filter_string in ['All', 'F', 'NF']:
                action = QAction(filter_string, group, checkable=True)
                if filter_string == 'All':
                    filter_string = None
                if filter_string == self.model().filters['flagging']:
                    action.setChecked(True)
                self.filter_menu.addAction(action)
                action.triggered.connect(get_filter_cb(key, filter_string))
                
        elif key == 'name':
            # Make button for resetting filter (show all).
            all_action = QAction('All', checkable=True)
            if not self.model().filters['name']:
                all_action.setChecked(True)
            all_action.triggered.connect(get_filter_cb(key, None))
            self.filter_menu.addAction(all_action) #add to menu
            self.filter_menu.addSeparator() #patch highlighting with mouse movement
            ## Make entry bar for name filter.
            # Create the entry bar with the existing filter as the text
            if self.name_hint:
                # Name in entry bar, if any
                text = self.name_hint
            else:
                # If no name in entry bar, name currently filtered by
                text = self.model().filters['name']
            entry = QLineEdit(text, self)
            entry.selectAll() #select all the text
            # Set focus to the entry bar when the menu is opened
            self.filter_menu.aboutToShow.connect(entry.setFocus)
            def set_name_filter():
                self.add_filter.emit(key, entry.text().strip())
                self.filter_menu.hide()
                self.block_header_menu = False
            entry.returnPressed.connect(set_name_filter) #enter applies filter
            name_action = QWidgetAction(self.filter_menu) #to contain QLineEdit
            name_action.setDefaultWidget(entry) #set widget on QWidgetAction
            self.filter_menu.addAction(name_action) #add to menu
        self.filter_menu.index = col
        # Display menu in appropriate position, below header in column 'col'
        headerPos = self.mapToGlobal(self.header.pos())
        posY = headerPos.y() + self.header.height()
        posX = headerPos.x() + self.header.sectionPosition(col)
        pos = QPoint(posX, posY)
        self.filter_menu.exec_(pos) #modal dialog
        self.resizeRowsToContents()
        
    def check_mouse_on_header_menu_hide(self):
        header_pos = self.mapToGlobal(self.header.pos())
        x_min = header_pos.x() + sum(
            [self.header.sectionSize(i) for i in range(self.filter_menu.index)])
        width = self.header.sectionSize(self.filter_menu.index)
        y_min = header_pos.y()
        height = self.mapToGlobal(self.index.pos()).y() - y_min
        if QRect(x_min, y_min, width, height).contains(QCursor.pos()):
            self.block_header_menu = True
        

class HighscoresModel(QAbstractTableModel):
    """
    Handles the sorting and filtering of the group of highscores being
    displayed.
    """
    sort_changed = pyqtSignal(int)
    def __init__(self, parent):
        super().__init__(parent)
        self.headers = ['name', 'time', '3bv', '3bv/s', 'date', 'flagging']
        self.all_data = [] #list of highscore dicts
        self.displayed_data = [] #filled in the filter_and_sort method
        self.active_hscore = None
        self.sort_index = 1 #sort by time by default
        # Initialise filters for each column.
        self.filters = {h: None for h in self.headers}
        # self.old_sort_index = self.old_filters = None
        self.update_hscores_group(
            HighscoreSettingsStruct.from_string(
                                    'diff=b,drag_select=False,per_cell=1')) #@@@
        
    # Overwrite methods
    def rowCount(self, parent=None):
        return len(self.displayed_data)
        
    def columnCount(self, parent=None):
        return len(self.headers)
        
    def data(self, index, role):
        header = self.headers[index.column()]
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole:
            return QVariant(self.format_data(index.row(), header))
        elif role == Qt.TextAlignmentRole:
            # if header in ['time', '3bv/s']:
            #     return QVariant(Qt.AlignRight | Qt.AlignVCenter)
            # else:
            return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
        elif role == Qt.FontRole:
            bold_font = QFont('Sans-serif', 8)
            bold_font.setBold(True)
            if index.row() == self.get_active_row():
                return bold_font
        else:
            return QVariant()
            
    def headerData(self, index, orientation, role):
        bold_font = QFont('Sans-serif', 9)
        bold_font.setBold(True)
        # Horizontal header
        if orientation == Qt.Horizontal:
            header = self.headers[index]
            if role == Qt.DisplayRole:
                return QVariant(header.capitalize())
            elif role == Qt.FontRole:
                if self.filters[header] or self.sort_index == index:
                    return bold_font
            elif role == Qt.SizeHintRole:
                # Set size hint for 'Name' column width (minimum width).
                if index == 0:
                    return QSize(200, 0)
        # Vertical indexing
        elif orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return QVariant(str(index + 1))
            elif role == Qt.FontRole:
                if index == self.get_active_row():
                    return bold_font
        return QVariant()
    
    def sort(self, index, order=Qt.DescendingOrder):
        header = self.headers[index]
        if header not in ['time', '3bv/s']:
            return
        self.sort_index = index
        self.filter_and_sort()
        self.sort_changed.emit(index)
        
    # New methods        
    # def apply_filters(self, filters, temp=False):
    #     for h, f in filters.items():
    #         self.filters[h] = f
    #     self.filter_and_sort()
    #     # if not temp and self.gui is not None:
    #     #     save_filters = self.gui.procr.hscore_filters
    #     #     for k, f in filters.items():
    #     #         save_filters[k] = f
    #     #     self.gui.set_highscore_settings(filters=save_filters) #unnecessary
            
    # def change_sort(self, sort_by, temp=False):
    #     """Argument sort_by can be column index or header string."""
    #     if type(sort_by) == int:
    #         self.sort_index = sort_by
    #         header = self.headers[sort_by]
    #     elif type(sort_by) == str:
    #         self.sort_index = self.headers.index(sort_by)
    #         header = sort_by
    #     self.filter_and_sort()
    #     # if not temp and self.gui is not None:
    #     #     self.gui.set_highscore_settings(sort_by=header)
            
    def update_hscores_group(self, settings):
        """
        Change the data to be highscores for a different set of settings.
        Arguments:
          settings (HighscoreSettingsStruct)
            Settings structure.
        """
        self.all_data = get_highscores(settings)
        self.filter_and_sort()
        
    def set_current_hscore(self, h):
        self.active_hscore = h
        # if h is None:
        #     # Restore old sort order and filters on new game
        #     self.change_sort(self.gui.procr.hscore_sort)
        #     self.apply_filters(self.gui.procr.hscore_filters)
        # #[Scroll to this hscore if get_active_row()]
        self.filter_and_sort()
        
    def get_active_row(self):
        if self.active_hscore in self.displayed_data:
            return self.displayed_data.index(self.active_hscore)
        else:
            return None
            
    def format_data(self, row, key):
        h = self.displayed_data[row]
        if key in ['name', 'date', 'flagging']:
            return h[key]
        elif key == 'time':
            # Convert to seconds and round up to nearest 100th of a second.
            return '{:6.2f}'.format(h['time'] / 1000 + 0.005)
        elif key == '3bv':
            return '{:3d}'.format(h['3bv']) #pad to 3 characters
        elif key == '3bv/s':
            # Round up to nearest 100th.
            return '{:.2f}'.format(h.get_3bvps() + 0.005)
        # elif key == 'date':
        #     return dt.date.fromtimestamp(h['date']).strftime('%d/%m/%y')
            
    def filter_and_sort(self):
        self.layoutAboutToBeChanged.emit()
        self.displayed_data = filter_and_sort(self.all_data,
                                              self.headers[self.sort_index],
                                              self.filters)
        self.layoutChanged.emit()



if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    settings = HighscoreSettingsStruct(**{'diff': 'b', 'drag_select': False, 'per_cell': 1}) #@@@
    hw = HighscoresWindow(None)
    hw.model.update_hscores_group(settings)
    hw.show()
    sys.exit(app.exec_())
