"""
types.py - Type definitions

June 2018, Lewis Gaul
"""

import enum
from collections import OrderedDict

from .utils import (Grid, CellState, GameCellMode, GameState, CellImageType,
    Struct)


class Board(Grid):
    """Board representation for handling displaying flags and openings."""
    def __init__(self, x_size, y_size):
        super().__init__(x_size, y_size, CellState.UNCLICKED)
        self.per_cell = 0
    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} board>"
    def __str__(self):
        def mapping(c):
            # Display openings with dashes.
            if c == 0:
                return '-'
            # Display the value from CellContents enum if it belongs to that class.
            if type(c) is CellState:
                if self.per_cell == 1:
                    return c.value[0]
                else:
                    return c.value
            return c
        return super().__str__(mapping, cell_size=2)

            
GameOptionsStruct = Struct('GameOptionsStruct',
                           x_size=8,
                           y_size=8,
                           mines=10,
                           first_success=True,
                           per_cell=1)
                
GUIOptionsStruct = Struct('GUIOptionsStruct',
                          name='',
                          btn_size=32,
                          styles={CellImageType.BUTTONS: 'standard',
                                  CellImageType.NUMBERS: 'standard',
                                  CellImageType.MARKERS: 'standard'},
                          drag_select=False)

class HighscoreSettingsStruct(Struct):
    elements = ['diff', 'drag_select', 'per_cell']
    restrictions = {'diff': ['b', 'i', 'e', 'm'],
                    'drag_select': bool,
                    'per_cell': [1, 2, 3]}
    def to_string(self):
        return ','.join(map(lambda k: f'{k}={self[k]}', self.elements))
    @classmethod
    def from_string(cls, string):
        valid = True
        try:
            elements = dict([elem.split('=') for elem in string.split(',')])
        except ValueError:
            valid = False
        if valid and len(elements) != len(cls.elements):
            valid = False
        if valid:
            for i, k in enumerate(elements):
                if k != cls.elements[i]:
                    valid = False
        if valid:
            if elements['drag_select'] == 'True':
                elements['drag_select'] = True
            elif elements['drag_select'] == 'False':
                elements['drag_select'] = False
            else:
                valid = False
            try:
                elements['per_cell'] = int(elements['per_cell'])
            except ValueError:
                valid = False
        if valid:
            return cls(**elements)
        else:
            raise ValueError("Invalid string for HighscoreSettingsStruct")

class HighscoreStruct(Struct):
    elements = ['name', 'time', '3bv', 'date', 'flagging', 'key']
    restrictions = {'name': str,
                    'time': int,
                    '3bv': int,
                    # 'date': str,
                    'flagging': ['F', 'NF']}
    def get_3bvps(self):
        return 1000 * self._3bv / self.time

class PersistSettingsStruct(Struct):
    elements = [*GameOptionsStruct.elements, *GUIOptionsStruct.elements]


