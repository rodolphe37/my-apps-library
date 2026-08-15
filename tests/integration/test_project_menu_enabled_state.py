"""Regression test for a real bug report: clicking Project -> "Modifier les
catégories..." (or any of the other selection-dependent Project menu items)
silently did nothing when no project was selected, with zero feedback -
main_window.py never disabled these actions based on selection, unlike the
context menu, which simply doesn't appear when nothing is selected.
"""

from PySide6.QtCore import QItemSelectionModel

from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.ui.main_window import MainWindow
from myapps.ui.theme.theme_manager import ThemeManager


def make_window(tmp_path, qtbot, qapp):
    pm = ProjectManager(path=tmp_path / "library.json")
    sm = SettingsManager(path=tmp_path / "settings.json")
    er = EditorRegistry(path=tmp_path / "editors.json")
    tm = ThemeManager(qapp)
    window = MainWindow(pm, sm, er, tm)
    qtbot.addWidget(window)
    return window, pm


def select_rows(window, rows: list[int]) -> None:
    window._selection_model.clearSelection()
    for row in rows:
        window._selection_model.select(
            window._model.index(row, 0), QItemSelectionModel.SelectionFlag.Select
        )


def test_project_menu_actions_disabled_with_no_selection(tmp_path, qtbot, qapp):
    window, _pm = make_window(tmp_path, qtbot, qapp)
    assert window._project_menu_actions  # sanity: the list got populated
    for action in window._project_menu_actions:
        assert not action.isEnabled()


def test_project_menu_actions_enable_on_selection(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)
    d = tmp_path / "proj"
    d.mkdir()
    pm.add_project(str(d))

    select_rows(window, [0])
    for action in window._project_menu_actions:
        assert action.isEnabled()


def test_project_menu_actions_disable_again_when_selection_cleared(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)
    d = tmp_path / "proj"
    d.mkdir()
    pm.add_project(str(d))

    select_rows(window, [0])
    window._selection_model.clearSelection()
    for action in window._project_menu_actions:
        assert not action.isEnabled()
