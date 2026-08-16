"""Covers the "Categories" section header CategorySidebar now inserts above
the category rows (see ui/widgets/category_sidebar.py's _make_section_header) -
it must stay purely visual: absent when there are no categories, never
selectable/current, and never confused with a real filter target by
_select_filter_id()/_current_filter_id()."""

from PySide6.QtCore import Qt

from myapps.core.project_manager import ProjectManager
from myapps.ui.widgets.category_sidebar import ALL_ITEM_ID, CategorySidebar


def make_sidebar(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    sidebar = CategorySidebar(pm)
    qtbot.addWidget(sidebar)
    return sidebar, pm


def test_no_header_when_no_categories(tmp_path, qtbot):
    sidebar, _pm = make_sidebar(tmp_path, qtbot)

    # All + Uncategorized only - no group header with nothing to group.
    assert sidebar.count() == 2
    assert sidebar.item(0).data(Qt.ItemDataRole.UserRole) == ALL_ITEM_ID


def test_header_appears_once_a_category_exists(tmp_path, qtbot):
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    pm.add_category("Python")

    # All (0), header (1), Python (2), Uncategorized (3).
    assert sidebar.count() == 4
    header = sidebar.item(1)
    assert header.data(Qt.ItemDataRole.UserRole) is None
    assert header.flags() == Qt.ItemFlag.NoItemFlags
    assert sidebar.item(0).data(Qt.ItemDataRole.UserRole) == ALL_ITEM_ID
    assert sidebar.item(2).data(Qt.ItemDataRole.UserRole) == pm.list_categories()[0].id


def test_forcing_current_onto_header_bounces_back_without_bad_filter(tmp_path, qtbot):
    """NoItemFlags keeps the header out of normal mouse/keyboard selection,
    but Qt's own setCurrentItem() API can still be called on it directly
    (see _on_current_changed's guard) - this must never surface as a
    filter_changed(None), which main_window.py would otherwise treat as
    "filter by Uncategorized"."""
    sidebar, pm = make_sidebar(tmp_path, qtbot)
    pm.add_category("Python")
    emitted: list[str] = []
    sidebar.filter_changed.connect(emitted.append)

    header = sidebar.item(1)
    sidebar.setCurrentItem(header)

    assert sidebar.currentItem() is not header
    assert None not in emitted
