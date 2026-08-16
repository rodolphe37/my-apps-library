"""Regression coverage for a real crash: hovering a grid tile could bring
down the whole app (a native segfault, not a catchable Python exception -
see ui/theme/shapes.py's paint_soft_shadow() docstring for the two riskier
implementations that caused this and were reverted). Drives a *real* grid
view through Qt's actual paint dispatch (qtbot + a shown widget + a
synthetic mouse move + processEvents()) rather than hand-building a
QStyledItemDelegate.paint() call directly - the latter was tried first and
turned out to be an unreliable way to reproduce/rule out this exact bug
(a segfault showed up from an unrelated-looking line, most likely an
artifact of bypassing the initialization a real QAbstractItemView gives
its delegate - not something worth chasing further when the real rendering
path is right here and already proven stable throughout this project's own
manual testing)."""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QMouseEvent

from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.ui.main_window import MainWindow
from myapps.ui.theme.theme_manager import ThemeManager


def test_hovering_every_grid_tile_does_not_crash(tmp_path, qtbot, qapp):
    pm = ProjectManager(path=tmp_path / "library.json")
    sm = SettingsManager(path=tmp_path / "settings.json")
    er = EditorRegistry(path=tmp_path / "editors.json")
    tm = ThemeManager(qapp)
    tm.set_mode("light")
    category = pm.add_category("Portfolio", icon="🔥")
    for i in range(4):
        project_dir = tmp_path / f"proj-{i}"
        project_dir.mkdir()
        project = pm.add_project(str(project_dir), name=f"proj-{i}")
        pm.set_categories(project.id, [category.id])
        if i == 0:
            pm.update_project(project.id, pinned=True)

    window = MainWindow(pm, sm, er, tm)
    qtbot.addWidget(window)
    window.resize(900, 600)
    window.show()
    window._set_active_view_mode("grid")
    qtbot.waitExposed(window)

    grid_view = window._views["grid"]
    viewport = grid_view.viewport()
    for row in range(window._model.rowCount()):
        rect = grid_view.visualRect(window._model.index(row, 0))
        center = rect.center()
        move = QMouseEvent(
            QEvent.Type.MouseMove,
            center,
            viewport.mapToGlobal(center),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        qapp.sendEvent(viewport, move)
        qapp.processEvents()

    # Reaching this line at all is the assertion - a segfault kills the
    # process before pytest can report a failure, so there's nothing to
    # additionally assert on; the window simply still being alive and
    # responsive is the proof.
    assert window.isVisible()
