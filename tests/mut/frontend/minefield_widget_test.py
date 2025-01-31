"""
minefield_widget_test.py - Test the minefield widget module

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k minefield_widget_test]'
from the root directory.
"""

from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtGui import QMouseEvent

from minegauler.frontend.minefield import MinefieldWidget


class TestMinefieldWidget:
    """
    There are the following sections of tests:
    Basic
        Creating the widget.
    Mouse clicks (drag select off, drag select on)
        Checking mouse actions trigger the correct controller calls. A
        controller mock is used with the spec of AbstractController. It is
        checked that expected calls are made, but in general no checks are made
        about unexpected calls (it is assumed this is an unlikely bug).
    """

    # Default button size to use.
    btn_size = 30
    # Callbacks for signals.
    at_risk_signal_cb = Mock()
    no_risk_signal_cb = Mock()
    # Store references to per-test created objects for convenience in helper
    #  functions.
    _qtbot = None
    _mf_widget = None
    _mouse_buttons_down = Qt.NoButton

    @pytest.fixture
    def mf_widget(self, qtbot, ctrlr):
        widget = MinefieldWidget(None, ctrlr, btn_size=self.btn_size)
        qtbot.addWidget(widget)
        widget.set_cell_image = Mock(wraps=widget.set_cell_image)
        widget.at_risk_signal.connect(self.at_risk_signal_cb)
        widget.no_risk_signal.connect(self.no_risk_signal_cb)
        widget.show()

        self._qtbot = qtbot
        self._mf_widget = widget
        self._mouse_buttons_down = Qt.NoButton
        self._mouse_down_pos = None

        yield widget

        self._qtbot = None
        self._mf_widget = None

    # --------------------------------------------------------------------------
    # Testcases
    # --------------------------------------------------------------------------
    def test_create(self, qtbot, ctrlr):
        widget = MinefieldWidget(None, ctrlr)
        qtbot.addWidget(widget)
        widget.show()

    def test_leftclick_no_drag(self, qtbot, mf_widget):
        """
        Test left-clicks with drag select off.
        """
        assert mf_widget.drag_select is False

        ## Basic left down and release on a cell.
        with qtbot.waitSignal(mf_widget.at_risk_signal):
            self.left_press((0, 1))
        self.assert_cell_sank((0, 1))
        self.left_release()
        mf_widget.ctrlr.select_cell.assert_called_with((0, 1))

        ## Mouse move.
        self.left_press((1, 0))
        # Move one cell away.
        self.mouse_move((2, 0))
        self.assert_cell_sank((2, 0))
        self.assert_cell_rose((1, 0))
        self.reset_mocks()
        # Move to corner of adjacent cell.
        self.mouse_move((3, 0), pos=(0, 0))
        self.assert_cell_sank((3, 0))
        self.assert_cell_rose((2, 0))
        self.reset_mocks()
        # Move to opposite corner of the same cell.
        self.mouse_move((3, 0), pos=(self.btn_size - 1, self.btn_size - 1))
        self.assert_cells_unchanged()
        self.reset_mocks()
        # Move off the board.
        self.mouse_move((3, -1))
        self.assert_cell_rose((3, 0))
        self.assert_num_cells_changed(1)
        self.reset_mocks()
        # Move back onto the board.
        self.mouse_move((0, 2))
        self.assert_cell_sank((0, 2))
        self.assert_num_cells_changed(1)
        self.reset_mocks()
        # Jump across board (supported?).
        self.mouse_move((7, 7))
        self.assert_cell_sank((7, 7))
        self.assert_cell_rose((0, 2))
        self.assert_num_cells_changed(2)
        self.reset_mocks()
        # Move off bottom edge.
        self.mouse_move((7, 8))
        self.assert_cell_rose((7, 7))
        self.assert_num_cells_changed(1)
        self.reset_mocks()
        # Move on at right edge.
        self.mouse_move((3, 7), pos=(self.btn_size // 2, self.btn_size - 1))
        self.assert_cell_sank((3, 7))
        self.assert_num_cells_changed(1)
        self.reset_mocks()
        # Release.
        self.left_release()
        mf_widget.ctrlr.select_cell.assert_called_with((3, 7))
        self.reset_mocks()

    def test_rightclick_no_drag(self, qtbot, mf_widget):
        """
        Test right-clicks with drag select off.
        """
        assert mf_widget.drag_select is False

        ## Basic right down and release on a cell.
        self.right_press((0, 1))
        mf_widget.ctrlr.flag_cell.assert_called_with((0, 1))
        self.at_risk_signal_cb.assert_not_called()
        self.reset_mocks()
        self.right_release()
        mf_widget.ctrlr.flag_cell.assert_not_called()

        ## Mouse move.
        self.right_press((1, 0))
        mf_widget.ctrlr.flag_cell.assert_called_with((1, 0))
        self.reset_mocks()
        # Move one cell away.
        self.mouse_move((2, 0))
        mf_widget.ctrlr.flag_cell.assert_not_called()
        self.reset_mocks()
        # Release.
        self.right_release()
        mf_widget.ctrlr.flag_cell.assert_not_called()
        self.reset_mocks()

    def test_chording_no_drag(self, qtbot, mf_widget):
        """
        Test chording clicks with drag select off.
        """
        assert mf_widget.drag_select is False

        ## Left down before right down.

    # --------------------------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------------------------
    def point_from_coord(self, coord, *, pos=None, btn_size=None):
        """
        Arguments:
        coord ((int, int))
            The coordinate to get the point for.
        pos=None ((int, int) | None)
            The position on the cell, defaults to the centre.
        btn_size=None (int | None)
            The button size in use. Defaults to the value stored on the class.

        Return: (QPoint)
            The QPoint corresponding to the passed-in coordinate.
        """
        if not btn_size:
            btn_size = self.btn_size
        if not pos:
            pos = (btn_size // 2, btn_size // 2)

        return QPoint(coord[0] * btn_size + pos[0], coord[1] * btn_size + pos[1])

    def left_press(self, coord=None, **kwargs):
        """
        Simulate a left mouse button press.

        Arguments:
        coord=None ((int, int) | None)
            The coordinate to click on, if the mouse is not already down.
        **kwargs
            Passed on to self._mouse_press().
        """
        self._mouse_press(Qt.LeftButton, coord, **kwargs)

    def left_release(self):
        """
        Simulate a left mouse button release.
        """
        self._mouse_release(Qt.LeftButton)

    def right_press(self, coord=None, **kwargs):
        """
        Simulate a right mouse button press.

        Arguments:
        coord=None ((int, int) | None)
            The coordinate to click on, if the mouse is not already down.
        **kwargs
            Passed on to self._mouse_press().
        """
        self._mouse_press(Qt.RightButton, coord, **kwargs)

    def right_release(self):
        """
        Simulate a right mouse button release.
        """
        self._mouse_release(Qt.RightButton)

    def mouse_move(self, coord, **kwargs):
        """
        Arguments:
        coord ((int, int))
            The coordinate to press down on.
        **kwargs
            Passed on to self.point_from_coord().
        """

        # The following line doesn't work, see QTBUG-5232.
        # self._qtbot.mouseMove(self._mf_widget.viewport(),
        #                       pos=self.point_from_coord(coord))

        pos = self.point_from_coord(coord, **kwargs)
        event = QMouseEvent(
            QEvent.MouseMove, pos, Qt.NoButton, self._mouse_buttons_down, Qt.NoModifier
        )
        self._mf_widget.mouseMoveEvent(event)
        self._mouse_down_pos = pos

    def assert_cell_sank(self, coord):
        self._mf_widget.set_cell_image.assert_any_call(coord, "btn_down")

    def assert_cell_rose(self, coord):
        self._mf_widget.set_cell_image.assert_any_call(coord, "btn_up")

    def assert_num_cells_changed(self, num):
        """
        Assert on the number of cells that had their image changed.
        """
        assert self._mf_widget.set_cell_image.call_count == num

    def assert_cells_unchanged(self):
        self._mf_widget.set_cell_image.assert_not_called()

    def reset_mocks(self):
        self._mf_widget.set_cell_image.reset_mock()
        self._mf_widget.ctrlr.reset_mock()
        self.at_risk_signal_cb.reset_mock()
        self.no_risk_signal_cb.reset_mock()

    def _mouse_press(self, button, coord=None, **kwargs):
        """
        Arguments:
        button (Qt.*Button)
            The mouse button to simulate a press for.
        coord=None ((int, int) | None)
            The coordinate to press down on, if the mouse is not already down.
        **kwargs
            Passed on to self.point_from_coord() if coord is given.
        """
        if self._mouse_buttons_down & button:
            raise RuntimeError("Mouse button already down, can't press again")
        if self._mouse_down_pos:
            if coord is not None:
                raise ValueError("Coord should not be given, mouse already down")
            pos = self._mouse_down_pos
        else:
            if coord is None:
                raise ValueError("Coord required, mouse is not down")
            pos = self.point_from_coord(coord, **kwargs)
        self._qtbot.mousePress(self._mf_widget.viewport(), button, pos=pos)
        self._mouse_buttons_down |= button
        self._mouse_down_pos = pos

    def _mouse_release(self, button):
        """
        Arguments:
        button (Qt.*Button)
            The mouse button to simulate a press for.
        """
        if not (self._mouse_buttons_down & button):
            raise RuntimeError("Mouse button isn't down, can't release")
        self._qtbot.mouseRelease(
            self._mf_widget.viewport(), button, pos=self._mouse_down_pos
        )
        self._mouse_buttons_down &= ~button
        if self._mouse_buttons_down == Qt.NoButton:
            self._mouse_down_pos = None
