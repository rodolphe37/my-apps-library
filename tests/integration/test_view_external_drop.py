"""Regression coverage for a reported bug: dragging folders in from Finder/
Explorer only imported them in grid view, not list view. Constructing a
real QDropEvent in Python is avoided deliberately - it has crashed via
libshiboken before in this codebase (see CategorySidebar.dropEvent's own
test, which delegates to a plain-Python method for the same reason). The
fix itself (ProjectListView.setAcceptDrops(True) + its own drag*/drop
overrides re-emitting external_folders_dropped) is exercised here at the
signal-wiring level instead.
"""

from PySide6.QtCore import Qt

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


def test_list_and_grid_views_both_accept_drops(tmp_path, qtbot, qapp):
    window, _pm = make_window(tmp_path, qtbot, qapp)
    for mode_id in ("list", "grid"):
        view = window._views[mode_id]
        assert view.testAttribute(Qt.WidgetAttribute.WA_AcceptDrops), (
            f"{mode_id} view does not accept drops"
        )


def test_list_and_grid_views_both_import_on_external_folders_dropped(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)

    for mode_id in ("list", "grid"):
        folder = tmp_path / f"proj-{mode_id}"
        folder.mkdir()
        view = window._views[mode_id]

        view.external_folders_dropped.emit([str(folder)])

        added = pm.find_by_path(str(folder))
        assert added is not None, f"dropping on the {mode_id} view didn't import the folder"
