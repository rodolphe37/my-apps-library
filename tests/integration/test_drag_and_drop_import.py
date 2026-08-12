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


def test_drop_multiple_folders_adds_all(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)
    dir_a = tmp_path / "proj-a"
    dir_b = tmp_path / "proj-b"
    dir_a.mkdir()
    dir_b.mkdir()

    window._add_projects_from_paths([str(dir_a), str(dir_b)])

    assert len(pm.list_projects()) == 2
    assert pm.find_by_path(str(dir_a)) is not None
    assert pm.find_by_path(str(dir_b)) is not None


def test_drop_skips_already_added_folder(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)
    dir_a = tmp_path / "proj-a"
    dir_a.mkdir()
    pm.add_project(str(dir_a))

    window._add_projects_from_paths([str(dir_a)])

    assert len(pm.list_projects()) == 1
