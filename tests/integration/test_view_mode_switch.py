from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.ui.main_window import MainWindow
from myapps.ui.models.project_list_model import ProjectIdRole
from myapps.ui.theme.theme_manager import ThemeManager


def make_window(tmp_path, qtbot, qapp):
    pm = ProjectManager(path=tmp_path / "library.json")
    sm = SettingsManager(path=tmp_path / "settings.json")
    er = EditorRegistry(path=tmp_path / "editors.json")
    tm = ThemeManager(qapp)
    window = MainWindow(pm, sm, er, tm)
    qtbot.addWidget(window)
    return window, pm


def test_selection_survives_view_mode_switch(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)
    dir_a = tmp_path / "proj-a"
    dir_b = tmp_path / "proj-b"
    dir_a.mkdir()
    dir_b.mkdir()
    pm.add_project(str(dir_a))
    target = pm.add_project(str(dir_b))

    # Select the second project's row via the shared selection model.
    index = window._model.index(1, 0)
    assert index.data(ProjectIdRole) == target.id
    window._selection_model.setCurrentIndex(
        index, window._selection_model.SelectionFlag.ClearAndSelect
    )
    assert window._current_project_id() == target.id

    window._set_active_view_mode("grid")
    assert window._current_project_id() == target.id

    window._set_active_view_mode("list")
    assert window._current_project_id() == target.id


def test_view_mode_persists_to_settings(tmp_path, qtbot, qapp):
    window, _pm = make_window(tmp_path, qtbot, qapp)
    window._set_active_view_mode("grid")
    assert window._settings.settings.view_mode == "grid"


def test_unknown_view_mode_falls_back_to_list(tmp_path, qtbot, qapp):
    window, _pm = make_window(tmp_path, qtbot, qapp)
    window._set_active_view_mode("does-not-exist")
    assert window._settings.settings.view_mode == "list"
    assert window._view_stack.currentWidget() is window._views["list"]


def test_view_mode_survives_a_real_restart(tmp_path, qtbot, qapp):
    """Regression test for a bug where MainWindow.__init__ itself silently
    reset+re-saved a persisted "grid" preference back to "list" on every
    startup (self._views was necessarily incomplete when the first
    registered view's signals were wired, which used to trigger a bogus
    "unknown view mode" fallback). A fresh SettingsManager + MainWindow
    pointed at the same settings.json, as a second launch would see, is
    what actually catches this — asserting against the same live window
    instance (as the other tests above do) can't."""
    settings_path = tmp_path / "settings.json"
    window1, _pm = make_window(tmp_path, qtbot, qapp)
    window1._set_active_view_mode("grid")
    assert SettingsManager(path=settings_path).settings.view_mode == "grid"

    window2, _pm2 = make_window(tmp_path, qtbot, qapp)
    assert window2._settings.settings.view_mode == "grid"
    assert window2._view_stack.currentWidget() is window2._views["grid"]
