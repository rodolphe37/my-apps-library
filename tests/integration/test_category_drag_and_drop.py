from PySide6.QtCore import Qt

from myapps.constants import UNCATEGORIZED_ID
from myapps.core.project_manager import ProjectManager
from myapps.ui.widgets.category_sidebar import ALL_ITEM_ID, CategorySidebar


def make_sidebar(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    sidebar = CategorySidebar(pm)
    qtbot.addWidget(sidebar)
    return sidebar, pm


def _item_for(sidebar, target_id):
    for row in range(sidebar.count()):
        item = sidebar.item(row)
        if item.data(Qt.ItemDataRole.UserRole) == target_id:
            return item
    raise AssertionError(f"No sidebar item for {target_id!r}")


def test_drop_on_category_replaces_categories(tmp_path, qtbot):
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cat_a = pm.add_category("Python")
    cat_b = pm.add_category("Web")
    project = pm.add_project(str(project_dir), categories=[cat_a.id])

    handled = sidebar._handle_drop(_item_for(sidebar, cat_b.id), project.id)

    assert handled is True
    assert pm.get_project(project.id).categories == [cat_b.id]


def test_drop_on_uncategorized_clears_categories(tmp_path, qtbot):
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cat_a = pm.add_category("Python")
    project = pm.add_project(str(project_dir), categories=[cat_a.id])

    handled = sidebar._handle_drop(_item_for(sidebar, UNCATEGORIZED_ID), project.id)

    assert handled is True
    assert pm.get_project(project.id).categories == []


def test_drop_on_all_is_noop(tmp_path, qtbot):
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cat_a = pm.add_category("Python")
    project = pm.add_project(str(project_dir), categories=[cat_a.id])

    handled = sidebar._handle_drop(_item_for(sidebar, ALL_ITEM_ID), project.id)

    assert handled is False
    assert pm.get_project(project.id).categories == [cat_a.id]


def test_drop_on_no_item_is_noop(tmp_path, qtbot):
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    project = pm.add_project(str(project_dir))

    handled = sidebar._handle_drop(None, project.id)

    assert handled is False


def test_drop_unknown_project_id_is_noop(tmp_path, qtbot):
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    cat_a = pm.add_category("Python")

    handled = sidebar._handle_drop(_item_for(sidebar, cat_a.id), "does-not-exist")

    assert handled is False


def test_drop_emits_recategorized_signal(tmp_path, qtbot):
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cat_a = pm.add_category("Python")
    project = pm.add_project(str(project_dir))

    with qtbot.waitSignal(sidebar.project_recategorized, timeout=1000) as blocker:
        sidebar._handle_drop(_item_for(sidebar, cat_a.id), project.id)
    assert blocker.args == [project.name, "Python"]
