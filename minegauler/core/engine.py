"""
engine.py - The core game logic

November 2018, Lewis Gaul

Exports:
Controller (class)
    Implementation of game logic and provision of functions to be called by a
    frontend implementation.
"""

import logging
from typing import Dict, Optional

import attr

from ..types import *
from ..typing import Coord_T
from . import api, board, game, utils


logger = logging.getLogger(__name__)


@attr.attrs(auto_attribs=True)
class SharedInfo:
    """
    Information to pass to frontends.
    
    Elements:
    cell_updates ({(int, int): CellContentsType, ...})
        Dictionary of updates to cells, mapping the coordinate to the new
        contents of the cell.
    game_state (GameState)
        The state of the game.
    mines_remaining (int)
        The number of mines remaining to be found, given by
        [total mines] - [number of flags]. Can be negative if there are too many
        flags. If the number is unchanged, None may be passed.
    lives_remaining (int)
        The number of lives remaining.
    elapsed_time (float | None)
        The time elapsed if the game has ended, otherwise None.
    """

    cell_updates: Dict[Coord_T, CellContentsType] = attr.Factory(dict)
    game_state: GameState = GameState.READY
    mines_remaining: int = 0
    lives_remaining: int = 0
    finish_time: Optional[float] = None


class Controller(api.AbstractController):
    """
    Class for processing all game logic. Implements functions defined in
    AbstractController that are called from UI.
    
    Attributes:
    opts (GameOptsStruct)
        Options for use in games.
    """

    def __init__(self, opts: utils.GameOptsStruct):
        """
        Arguments:
        opts (GameOptsStruct)
            Object containing the required game options as attributes.
        """
        super().__init__(opts)

        self._game: Optional[game.Game] = None
        self._last_update: SharedInfo

        self.new_game()

    @property
    def board(self) -> board.Board:
        return self._game.board

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def new_game(self) -> None:
        """See AbstractController."""
        super().new_game()
        self._game = game.Game(
            x_size=self.opts.x_size,
            y_size=self.opts.y_size,
            mines=self.opts.mines,
            per_cell=self.opts.per_cell,
            lives=self.opts.lives,
            first_success=self.opts.first_success,
        )
        self._send_reset_update()

    def restart_game(self) -> None:
        """See AbstractController."""
        if not self._game.mf:
            return
        super().restart_game()
        self._game = game.Game(minefield=self._game.mf, lives=self.opts.lives)
        self._send_reset_update()

    def select_cell(self, coord: Coord_T) -> None:
        """See AbstractController."""
        super().select_cell(coord)
        cells = self._game.select_cell(coord)
        self._send_updates(cells)

    def flag_cell(self, coord: Coord_T, *, flag_only: bool = False) -> None:
        """See AbstractController."""
        super().flag_cell(coord)

        cell_state = self._game.board[coord]
        if cell_state is CellUnclicked():
            self._game.set_cell_flags(coord, 1)
        elif isinstance(cell_state, CellFlag):
            if cell_state.num == self.opts.per_cell:
                if flag_only:
                    return
                self._game.set_cell_flags(coord, 0)
            else:
                self._game.set_cell_flags(coord, cell_state.num + 1)

        self._send_updates({coord: self._game.board[coord]})

    def remove_cell_flags(self, coord: Coord_T) -> None:
        """See AbstractController."""
        super().remove_cell_flags(coord)
        self._game.set_cell_flags(coord, 0)
        self._send_updates({coord: self._game.board[coord]})

    def chord_on_cell(self, coord: Coord_T) -> None:
        """See AbstractController."""
        super().chord_on_cell(coord)
        cells = self._game.chord_on_cell(coord)
        self._send_updates(cells)

    def resize_board(self, *, x_size: int, y_size: int, mines: int) -> None:
        """See AbstractController."""
        super().resize_board(x_size, y_size, mines)
        if (
            x_size == self.opts.x_size
            and y_size == self.opts.y_size
            and mines == self.opts.mines
        ):
            logger.info(
                "No resize required as the parameters are unchanged, starting a new game"
            )
            self.new_game()
            return

        logger.info(
            "Resizing board from %sx%s with %s mines to %sx%s with %s mines",
            self.opts.x_size,
            self.opts.y_size,
            self.opts.mines,
            x_size,
            y_size,
            mines,
        )
        self.opts.x_size = x_size
        self.opts.y_size = y_size
        self.opts.mines = mines
        self._send_resize_update()
        self.new_game()

    def set_first_success(self, value: bool) -> None:
        """
        Set whether the first click should be a guaranteed success.
        """
        super().set_first_success(value)
        self.opts.first_success = value

    def set_per_cell(self, value: int) -> None:
        """
        Set the maximum number of mines per cell.
        """
        super().set_per_cell(value)
        if self.opts.per_cell != value:
            self.opts.per_cell = value
            if self._game.state.unstarted():
                self.new_game()

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    def _send_reset_update(self) -> None:
        self._notif.reset()
        self._last_update = SharedInfo()
        self._cells_updated = dict()

    def _send_resize_update(self) -> None:
        self._notif.resize(self.opts.x_size, self.opts.y_size, self.opts.mines)

    def _send_updates(self, cells_updated: Dict[Coord_T, CellContentsType]) -> None:
        """Send updates to registered listeners."""
        update = SharedInfo(
            cell_updates=cells_updated,
            mines_remaining=self._game.mines_remaining,
            lives_remaining=self._game.lives_remaining,
            game_state=self._game.state,
            finish_time=self._game.get_elapsed() if self._game.is_finished() else None,
        )

        if update.cell_updates:
            self._notif.update_cells(update.cell_updates)
        if update.mines_remaining != self._last_update.mines_remaining:
            self._notif.update_mines_remaining(update.mines_remaining)
        # if update.lives_remaining != self._last_update.lives_remaining:
        #     self._notif.update_lives_remaining(update.lives_remaining)
        if update.game_state is not self._last_update.game_state:
            self._notif.update_game_state(update.game_state)
        if (
            update.finish_time is not None
            and update.finish_time != self._last_update.finish_time
        ):
            self._notif.set_finish_time(update.finish_time)

        self._last_update = update
