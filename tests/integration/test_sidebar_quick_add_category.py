"""Covers the sidebar footer's "+ Add category" button
(MainWindow._build_sidebar_footer/_quick_add_category) - a fast QInputDialog
prompt, deliberately distinct from the toolbar's "Add Project" button and
from the full Project > Manage Categories… dialog."""

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


def test_quick_add_category_creates_category(tmp_path, qtbot, qapp, monkeypatch):
    window, pm = make_window(tmp_path, qtbot, qapp)
    monkeypatch.setattr(
        "myapps.ui.main_window.QInputDialog.getText", lambda *a, **k: ("Design", True)
    )

    window._quick_add_category()

    assert [c.name for c in pm.list_categories()] == ["Design"]


def test_quick_add_category_cancelled_adds_nothing(tmp_path, qtbot, qapp, monkeypatch):
    window, pm = make_window(tmp_path, qtbot, qapp)
    monkeypatch.setattr(
        "myapps.ui.main_window.QInputDialog.getText", lambda *a, **k: ("", False)
    )

    window._quick_add_category()

    assert pm.list_categories() == []


def test_quick_add_category_blank_name_adds_nothing(tmp_path, qtbot, qapp, monkeypatch):
    window, pm = make_window(tmp_path, qtbot, qapp)
    monkeypatch.setattr(
        "myapps.ui.main_window.QInputDialog.getText", lambda *a, **k: ("   ", True)
    )

    window._quick_add_category()

    assert pm.list_categories() == []
