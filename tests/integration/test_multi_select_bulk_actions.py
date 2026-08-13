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


def test_selected_project_ids_reflects_multi_selection(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)
    projects = []
    for i in range(3):
        d = tmp_path / f"proj-{i}"
        d.mkdir()
        projects.append(pm.add_project(str(d)))

    assert window._selected_project_ids() == []

    select_rows(window, [0, 2])
    selected = set(window._selected_project_ids())
    assert selected == {projects[0].id, projects[2].id}


def test_bulk_pin_pins_every_selected_project(tmp_path, qtbot, qapp):
    window, pm = make_window(tmp_path, qtbot, qapp)
    ids = []
    for i in range(3):
        d = tmp_path / f"proj-{i}"
        d.mkdir()
        ids.append(pm.add_project(str(d)).id)

    window._toggle_pin_bulk(ids, pin=True)
    assert all(pm.get_project(pid).pinned for pid in ids)

    window._toggle_pin_bulk(ids, pin=False)
    assert not any(pm.get_project(pid).pinned for pid in ids)


def test_bulk_remove_removes_every_selected_project(tmp_path, qtbot, qapp, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    window, pm = make_window(tmp_path, qtbot, qapp)
    ids = []
    for i in range(3):
        d = tmp_path / f"proj-{i}"
        d.mkdir()
        ids.append(pm.add_project(str(d)).id)

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes)
    window._remove_bulk(ids)

    assert pm.list_projects() == []


def test_bulk_remove_declined_keeps_projects(tmp_path, qtbot, qapp, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    window, pm = make_window(tmp_path, qtbot, qapp)
    ids = []
    for i in range(2):
        d = tmp_path / f"proj-{i}"
        d.mkdir()
        ids.append(pm.add_project(str(d)).id)

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.No)
    window._remove_bulk(ids)

    assert len(pm.list_projects()) == 2


def test_edit_categories_for_selection_uses_bulk_dialog_when_multiple_selected(
    tmp_path, qtbot, qapp, monkeypatch
):
    window, pm = make_window(tmp_path, qtbot, qapp)
    ids = []
    for i in range(2):
        d = tmp_path / f"proj-{i}"
        d.mkdir()
        ids.append(pm.add_project(str(d)).id)
    select_rows(window, [0, 1])

    called_with = {}

    def fake_bulk(project_ids):
        called_with["ids"] = set(project_ids)

    monkeypatch.setattr(window, "_edit_categories_bulk", fake_bulk)
    window._edit_categories_for_selection()

    assert called_with["ids"] == set(ids)


def test_edit_categories_for_selection_uses_single_dialog_for_one_project(
    tmp_path, qtbot, qapp, monkeypatch
):
    window, pm = make_window(tmp_path, qtbot, qapp)
    d = tmp_path / "proj-solo"
    d.mkdir()
    project = pm.add_project(str(d))
    select_rows(window, [0])
    window._selection_model.setCurrentIndex(
        window._model.index(0, 0), QItemSelectionModel.SelectionFlag.Current
    )

    called_with = {}
    monkeypatch.setattr(window, "_edit_categories", lambda pid: called_with.setdefault("id", pid))
    window._edit_categories_for_selection()

    assert called_with["id"] == project.id
