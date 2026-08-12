from PySide6.QtCore import Qt

from myapps.core.project_manager import ProjectManager
from myapps.ui.delegates.project_item_delegate import ProjectItemDelegate
from myapps.ui.models.project_list_model import (
    PinnedRole,
    ProjectIdRole,
    ProjectListModel,
    ProjectPathRole,
)


def test_model_reflects_added_project(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    assert model.rowCount() == 0

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    project = pm.add_project(str(project_dir))

    assert model.rowCount() == 1
    index = model.index(0, 0)
    assert index.data(Qt.ItemDataRole.DisplayRole) == "proj"
    assert index.data(ProjectIdRole) == project.id
    assert index.data(ProjectPathRole) == project.path
    assert index.data(PinnedRole) is False


def test_model_removes_on_project_removed(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    project = pm.add_project(str(project_dir))
    assert model.rowCount() == 1

    pm.remove_project(project.id)
    assert model.rowCount() == 0


def test_model_category_filter(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    dir_a, dir_b = tmp_path / "a", tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    project_a = pm.add_project(str(dir_a))
    pm.add_project(str(dir_b))
    cat = pm.add_category("Python")
    pm.set_categories(project_a.id, [cat.id])

    model.set_category_filter(cat.id)
    assert model.rowCount() == 1
    assert model.index(0, 0).data(ProjectIdRole) == project_a.id

    model.clear_filter()
    assert model.rowCount() == 2


def test_delegate_paints_without_error(tmp_path, qtbot):
    from PySide6.QtGui import QPainter, QPixmap
    from PySide6.QtWidgets import QStyleOptionViewItem

    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    pm.add_project(str(project_dir))

    delegate = ProjectItemDelegate(pm)
    pixmap = QPixmap(200, 60)
    painter = QPainter(pixmap)
    try:
        option = QStyleOptionViewItem()
        option.rect = pixmap.rect()
        delegate.paint(painter, option, model.index(0, 0))
    finally:
        painter.end()
