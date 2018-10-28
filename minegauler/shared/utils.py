"""
utils.py - General utils

March 2018, Lewis Gaul
"""

from os.path import dirname, abspath, join
import enum
from types import SimpleNamespace, MethodType
try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle
import logging


logger = logging.getLogger(__name__)


def get_curdir(fpath):
    return dirname(abspath(fpath))

root_dir = dirname(get_curdir(__file__))
files_dir = join(root_dir, 'files')
highscores_dir = join(files_dir, 'highscores')


def ASSERT(condition, message=""):
    """The built-in assert as a function."""
    assert condition, message
    

def read_settings():
    with open(join(files_dir, 'settings.cfg'), 'rb') as f:
        return pickle.load(f)


def save_settings(settings):
    """
    Save settings to 'settings.cfg' file in JSON format.
    Arguments:
      settings (dict)
        Dictionary of settings to save.
    """
    logger.info("Saving settings to file: %s", settings)
    with open(join(files_dir, 'settings.cfg'), 'wb') as f:
        pickle.dump(settings, f)


class AddEnum(enum.Enum):
    def __add__(self, obj):
        if type(obj) is int:
            return getattr(self,
                self.name[:-1] + str(self.num + obj))
        raise TypeError("unsupported operand type(s) for +: "
                        "'{}' and '{}'".format(type(self).__name__,
                                               type(obj).__name__))
    @property
    def num(self):
        return int(self.value[-1])

#@@@
CellState = AddEnum('CellState',
                    {'UNCLICKED': '#',
                     **{'NUM%d' % i : 'N%d' % i for i in range(21)},
                     **{'FLAG%d' % i : 'F%d' % i for i in range(1, 11)},
                     **{'CROSS%d' % i : 'X%d' % i for i in range(1, 11)},
                     **{'MINE%d' % i : 'M%d' % i for i in range(1, 11)},
                     **{'HIT%d' % i : 'H%d' % i for i in range(1, 11)},
                     # **{'LIFE%d' % i : 'L%d' % i for i in range(1, 11)},
                     'SPLIT': '+'
                    })
CellState.NUMS    = [getattr(CellState, 'NUM%d' % i) for i in range(21)]
CellState.FLAGS   = [None,
                     *[getattr(CellState, 'FLAG%d' % i) for i in range(1, 11)]
                    ]
CellState.CROSSES = [None,
                     *[getattr(CellState, 'CROSS%d' % i) for i in range(1, 11)]
                    ]
CellState.MINES   = [None,
                     *[getattr(CellState, 'MINE%d' % i) for i in range(1, 11)]
                    ]
CellState.HITS    = [None,
                     *[getattr(CellState, 'HIT%d' % i) for i in range(1, 11)]
                    ]
# CellState.LIVES   = {i: getattr(CellState, 'LIFE%d' % i) for i in range(1, 11)}


class GameState(enum.Enum):
    READY = enum.auto()
    ACTIVE = enum.auto()
    WON = enum.auto()
    LOST = enum.auto()
    

class GameCellMode(enum.Enum):
    """
    The layout and behaviour modes for the cells.
    """
    NORMAL = 'Original style'
    SPLIT = 'Cells split instead of flagging'
    SPLIT1 = SPLIT
    SPLIT2 = 'Cells split twice'
    

class CellImageType(enum.Flag):
    BUTTONS = enum.auto()
    NUMBERS = enum.auto()
    MARKERS = enum.auto()
    ALL = BUTTONS | NUMBERS | MARKERS


class Grid(list):
    """Grid representation using a list of lists (2D array)."""
    def __init__(self, x_size, y_size, fill=0):
        """
        Arguments:
          x_size (int > 0)
            The number of columns.
          y_size (int > 0)
            The number of rows.
          fill=0 (object)
            What to fill the grid with.
        """
        super().__init__()
        for j in range(y_size):
            row = x_size * [fill]
            self.append(row)
        self.x_size, self.y_size = x_size, y_size
        self.all_coords = [(x, y) for x in range(x_size) for y in range(y_size)]

    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} grid>"

    def __str__(self, mapping=None, cell_size=None):
        """
        Convert the grid to a string in an aligned format. The __repr__ method
        is used to display the objects inside the grid unless the mapping
        argument is given.
        Arguments:
          mapping=None (dict | callable | None)
            A mapping to apply to all objects contained within the grid. The
            result of the mapping will be converted to a string and displayed.
            If a mapping is specified, a cell size should also be given.
          cell_size=None (int | None)
            The size to display a grid cell as. Defaults to the maximum size of
            the representation of all the objects contained in the grid.
        """
        # Convert dict mapping to function.
        if type(mapping) is dict:
            mapping = lambda obj: mapping[obj] if obj in mapping else obj
        # Use max length of object representation if no cell size given.
        if cell_size is None:
            cell_size = max(
                           [len(obj.__repr__()) for row in self for obj in row])
        cell = '{:>%d}' % cell_size
        ret = ''
        for row in self:
            for obj in row:
                if mapping is not None:
                    repr = str(mapping(obj))
                else:
                    repr = obj.__repr__()
                ret += cell.format(repr[:cell_size]) + ' '
            ret = ret[:-1] # Remove trailing space
            ret += '\n'
        ret = ret[:-1] # Remove trailing newline
        return ret

    def __getitem__(self, key):
        if type(key) is tuple and len(key) == 2:
            return self[key[1]][key[0]]
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        if type(key) is tuple and len(key) == 2:
            self[key[1]][key[0]] = value
        else:
            super().__setitem__(key, value)
            
    def fill(self, item):
        """
        Fill the grid with a given object.
        Arguments:
          item (object)
            The item to fill the grid with.
        """
        for row in self:
            for i in range(len(row)):
                row[i] = item

    def get_nbrs(self, x, y, include_origin=False):
        """
        Get a list of the coordinates of neighbouring cells.
        Arguments:
          x (int, 0 <= x <= self.x_size)
            x-coordinate
          y (int, 0 <= y <= self.y_size)
            y-coordinate
          include_origin=False (bool)
            Whether to include the original coordinate, (x, y), in the list.
        Return: [(int, int), ...]
            List of coordinates within the boundaries of the grid.
        """
        nbrs = []
        for i in range(max(0, x - 1), min(self.x_size, x + 2)):
            for j in range(max(0, y - 1), min(self.y_size, y + 2)):
                nbrs.append((i, j))
        if not include_origin:
            nbrs.remove((x, y))
        return nbrs


def strip_leading_uscore(string):
    if string[0] == '_':
        string = string[1:]
    return string

class Struct(dict):
    """
    Base class for data structures with generator functionality as in enum.Enum.
    Data is stored in an ordered dictionary and is also accessible through
    attributes - keys must be valid variable names, however elements with a
    single preceding underscore will have the underscore removed for the
    dictionary key, allowing keys which begin with a digit.
    Example usage:
    MyStruct = Struct('MyStruct', elem1=None, _2nd_elem=[])
    s1 = MyStruct(elem1=1)        # s1: {'elem1': 1, '2nd_elem': []}
    
    Note that dictionaries preserve order in CPython3.6 and PEP468 assures that
    **kwargs will have their order preserved.
    """
    #@@@For when dict ordering is not 'supported', OrderedDict should be
    #subclassed instead.
    # List of elements.
    elements = []
    # Optional mapping of elements to their defaults.
    defaults = {}
    # Optional mapping of elements to a restriction for valid values, which can
    #  be either a set of valid values or a function returning a boolean for
    #  whether a value is valid.
    restrictions = {}
    def __init__(self, **kwargs):
        super().__init__()
        # Allow keys which start with a number by using a preceding underscore.
        for k, v in kwargs.items():
            self[strip_leading_uscore(k)] = v
        # Set remaining elements to defaults.
        for k, v in self.defaults.items():
            if k not in self.elements:
                raise ValueError("Invalid element name in defaults mapping")
            elif k not in self:
                self[k] = v
    def __new__(cls, _name=None, **kwargs):
        if cls.__name__ == 'Struct':
            if not isinstance(_name, str):
                raise ValueError("Creating a new struct class requires a class "
                                 "name")
            struct = type(_name, (Struct,), {})
            struct.elements = []
            struct.defaults = {}
            struct.restrictions = {}
            for k, v in kwargs.items():
                k = strip_leading_uscore(k)
                struct.elements.append(k)
                struct.defaults[k] = v
            return struct
        else:
            return super().__new__(cls)
    def __getitem__(self, key):
        if key not in self.elements:
            raise KeyError("Unexpected element")
        if key in self:
            return super().__getitem__(key)
        else:
            return None
    def __setitem__(self, key, value):
        if key not in self.elements:
            raise KeyError("Unexpected element")
        elif key in self.restrictions and value is not None:
            invalidity = None
            if isinstance(self.restrictions[key], (tuple, list, set)):
                if value not in self.restrictions[key]:
                    invalidity = "not in set"
            elif type(self.restrictions[key]) is type:
                if not isinstance(value, self.restrictions[key]):
                    invalidity = "wrong type"
            else:
                try:
                    if not self.restrictions[key](value):
                        invalidity = "validity function returned False"
                except TypeError:
                    logger.warn("Unexpected restriction type for %s:"
                                "{%s: %s}",
                                type(self).__name__,
                                key,
                                self.restrictions[key])
            if invalidity is not None:
                raise ValueError("Invalid value as determined by "
                                 "'restrictions': {}".format(invalidity))
        super().__setitem__(key, value)
    def __getattr__(self, key):
        if type(key) is MethodType:
            super().__getattr(key)
        # Allow keys which start with a number by using a preceding underscore.
        key = strip_leading_uscore(key)
        if key not in self.elements:
            raise AttributeError("Unexpected element")
        return self[key]
    def __setattr__(self, key, value):
        # Allow keys which start with a number by using a preceding underscore.
        key = strip_leading_uscore(key)
        if key not in self.elements:
            raise AttributeError("Unexpected element")
        self[key] = value
        
        
