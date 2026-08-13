from PySide6.QtCore import Qt

from myapps.core.project_manager import ProjectManager
from myapps.ui.dialogs.category_manager_dialog import BulkCategoryPickerDialog


def make_projects(tmp_path, pm: ProjectManager, n: int):
    projects = []
    for i in range(n):
        d = tmp_path / f"proj-{i}"
        d.mkdir()
        projects.append(pm.add_project(str(d)))
    return projects


def test_checkbox_reflects_full_partial_and_no_membership(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    cat_all = pm.add_category("All three")
    cat_some = pm.add_category("Some")
    cat_none = pm.add_category("None")
    p0, p1, p2 = make_projects(tmp_path, pm, 3)

    pm.set_categories(p0.id, [cat_all.id, cat_some.id])
    pm.set_categories(p1.id, [cat_all.id])
    pm.set_categories(p2.id, [cat_all.id])
    projects = [pm.get_project(p.id) for p in (p0, p1, p2)]

    dialog = BulkCategoryPickerDialog(projects, pm, None)
    qtbot.addWidget(dialog)

    states = {
        dialog._list.item(row).data(Qt.ItemDataRole.UserRole): dialog._list.item(row).checkState()
        for row in range(dialog._list.count())
    }
    assert states[cat_all.id] == Qt.CheckState.Checked
    assert states[cat_some.id] == Qt.CheckState.PartiallyChecked
    assert states[cat_none.id] == Qt.CheckState.Unchecked


def test_apply_adds_removes_and_leaves_partial_untouched(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    cat_all = pm.add_category("All three")
    cat_some = pm.add_category("Some")
    cat_none = pm.add_category("None")
    p0, p1, p2 = make_projects(tmp_path, pm, 3)

    pm.set_categories(p0.id, [cat_all.id, cat_some.id])
    pm.set_categories(p1.id, [cat_all.id])
    pm.set_categories(p2.id, [cat_all.id])
    projects = [pm.get_project(p.id) for p in (p0, p1, p2)]

    dialog = BulkCategoryPickerDialog(projects, pm, None)
    qtbot.addWidget(dialog)

    def item_for(category_id):
        for row in range(dialog._list.count()):
            item = dialog._list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == category_id:
                return item
        raise AssertionError("category not found")

    # Explicitly uncheck the universally-held category, explicitly check the
    # unheld one, and leave the partially-held one exactly as it started.
    item_for(cat_all.id).setCheckState(Qt.CheckState.Unchecked)
    item_for(cat_none.id).setCheckState(Qt.CheckState.Checked)

    dialog.apply()

    for pid in (p0.id, p1.id, p2.id):
        refreshed = pm.get_project(pid)
        assert cat_all.id not in refreshed.categories
        assert cat_none.id in refreshed.categories

    # cat_some's original, heterogeneous membership is untouched.
    assert cat_some.id in pm.get_project(p0.id).categories
    assert cat_some.id not in pm.get_project(p1.id).categories
    assert cat_some.id not in pm.get_project(p2.id).categories


def test_apply_is_a_noop_when_nothing_changes(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    cat = pm.add_category("Untouched")
    (p0,) = make_projects(tmp_path, pm, 1)
    pm.set_categories(p0.id, [cat.id])
    projects = [pm.get_project(p0.id)]

    dialog = BulkCategoryPickerDialog(projects, pm, None)
    qtbot.addWidget(dialog)

    calls = []
    monkeypatch.setattr(pm, "set_categories", lambda *a, **kw: calls.append((a, kw)))
    dialog.apply()
    assert calls == []
