"""
utils.py - GUI utils

April 2018, Lewis Gaul
"""

from os.path import join, exists, dirname, abspath
import logging
import enum

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QImage

from minegauler.shared import get_curdir, CellState, CellImageType


logger = logging.getLogger(__name__)

img_dir = join(get_curdir(__file__), 'images')


class FaceState(enum.Enum):
    READY  = 'ready'
    ACTIVE = 'active'
    WON    = 'won'
    LOST   = 'lost'
    

def init_or_update_cell_images(cell_images, size, styles,
                               required=CellImageType.ALL):
    """
    Initialise or update the pixmap images for the minefield cells.
    Arguments:
      cell_images (dict)
        The dictionary to fill with the images.
      size (int)
        The size in pixels to make the image (square).
      required (CellImageType)
        Which images types require updating.
    """
    #@@@ Currently only allows setting button styles.
    btn_style = styles[CellImageType.BUTTONS]
    if required & CellImageType.BUTTONS:
        cell_images['btn_up'] = make_pixmap('buttons',
                                            btn_style,
                                            'btn_up.png',
                                            size)
        cell_images['btn_down'] = make_pixmap('buttons',
                                              btn_style,
                                              'btn_down.png',
                                              size)
        cell_images[CellState.UNCLICKED] = cell_images['btn_up']
        cell_images[CellState.NUM0] = cell_images['btn_down']
        
    if required & (CellImageType.BUTTONS | CellImageType.NUMBERS):
        for i in range(1, 19):
            cell_images[CellState.NUMS[i]] = make_pixmap('numbers',
                                                         btn_style,
                                                         'btn_down.png',
                                                         size,
                                                         'num%d.png' % i,
                                                         7/8)
                                                         
    if required & (CellImageType.BUTTONS | CellImageType.MARKERS):
        for i in range(1, 4):
            cell_images[CellState.FLAGS[i]] = make_pixmap('markers',
                                                          btn_style,
                                                          'btn_up.png',
                                                          size,
                                                          'flag%d.png' % i,
                                                          5/8)
            cell_images[CellState.CROSSES[i]] = make_pixmap('markers',
                                                            btn_style,
                                                            'btn_up.png',
                                                            size,
                                                            'cross%d.png' % i,
                                                            5/8)
            cell_images[CellState.MINES[i]] = make_pixmap('markers',
                                                          btn_style,
                                                          'btn_down.png',
                                                          size,
                                                          'mine%d.png' % i,
                                                          7/8)
            cell_images[CellState.HITS[i]] = make_pixmap('markers',
                                                         btn_style,
                                                         'btn_down_hit.png',
                                                         size,
                                                         'mine%d.png' % i,
                                                         7/8)
            # cell_images['life'][i] = make_pixmap('markers',
            #                                      btn_style,
            #                                      'btn_down_life.png',
            #                                      size,
            #                                      'mine%d.png' % i,
            #                                      7/8)
        
        
def make_pixmap(img_subdir, style, bg_fname, size, fg_fname=None, propn=1):
    def get_path(subdir, fname, style):
        base_path = join(img_dir, subdir)
        full_path = join(base_path, style, fname)
        if not exists(full_path):
            logger.warn(
                f'Missing image file at {full_path}, using standard style')
            full_path = join(base_path, 'standard', fname)
        return full_path
    bg_path = get_path('buttons', bg_fname, style)
    if fg_fname:
        image = QImage(bg_path).scaled(size, size,
                                       transformMode=Qt.SmoothTransformation)
        fg_size = propn * size
        fg_path = get_path(img_subdir, fg_fname, 'standard')
        overlay = QPixmap(fg_path).scaled(fg_size, fg_size,
                                          transformMode=Qt.SmoothTransformation)
        painter = QPainter(image)
        margin = size * (1 - propn) / 2
        painter.drawPixmap(margin, margin, overlay)
        painter.end()
        image = QPixmap.fromImage(image)
    else:
        image = QPixmap(bg_path).scaled(size, size,
                                        transformMode=Qt.SmoothTransformation)
    return image