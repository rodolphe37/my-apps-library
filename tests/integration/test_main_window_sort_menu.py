"""Regression test for a real crash: the Sort By submenu's actions were
wired to _set_sort_key/_set_sort_descending in _build_menu_bar() before
those methods existed on MainWindow, so simply launching the app raised
AttributeError. Exercising the menu construction (not just the model-level
sort logic covered by test_project_sort.py) is what would have caught it.
"""

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
    return window, pm, sm


def test_window_constructs_without_raising(tmp_path, qtbot, qapp):
    # The bug: this alone used to raise AttributeError during
    # _build_menu_bar(), before the window ever became usable.
    make_window(tmp_path, qtbot, qapp)


def test_set_sort_key_persists_and_resorts(tmp_path, qtbot, qapp):
    window, pm, sm = make_window(tmp_path, qtbot, qapp)
    for name in ("bravo", "alpha"):
        d = tmp_path / name
        d.mkdir()
        pm.add_project(str(d), name=name)

    window._set_sort_key("name")
    assert sm.settings.sort_key == "name"
    assert window._model.index(0, 0).data() == "alpha"


def test_set_sort_descending_persists_and_resorts(tmp_path, qtbot, qapp):
    window, pm, sm = make_window(tmp_path, qtbot, qapp)
    for name in ("bravo", "alpha"):
        d = tmp_path / name
        d.mkdir()
        pm.add_project(str(d), name=name)
    window._set_sort_key("name")

    window._set_sort_descending(True)
    assert sm.settings.sort_direction == "desc"
    assert window._model.index(0, 0).data() == "bravo"

    window._set_sort_descending(False)
    assert sm.settings.sort_direction == "asc"
    assert window._model.index(0, 0).data() == "alpha"


def test_sort_setting_survives_reload(tmp_path, qtbot, qapp):
    window, pm, sm = make_window(tmp_path, qtbot, qapp)
    window._set_sort_key("created_at")
    window._set_sort_descending(True)

    sm2 = SettingsManager(path=tmp_path / "settings.json")
    assert sm2.settings.sort_key == "created_at"
    assert sm2.settings.sort_direction == "desc"
