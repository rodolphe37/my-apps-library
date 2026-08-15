"""Left sidebar: All / Uncategorized / each category, for filtering the
project list. Emits `category_selected(category_id_or_None)`; a sentinel
string "__all__" is translated to None-with-no-filter by main_window.

Also accepts drops of a project dragged from the list/grid view (see
ui/models/project_list_model.py's PROJECT_ID_MIME_TYPE and
ui/views/project_list_view.py's drag-enabled setup): dropping a project onto
a category here *replaces* its categories with just that one - a "move into
folder" semantic, distinct from the checkbox-based multi-category assignment
in Project > Edit Categories…, which is still there for tagging a project
into several categories at once.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from myapps.constants import UNCATEGORIZED_ID
from myapps.core.events import event_bus
from myapps.core.project_manager import ProjectManager
from myapps.i18n import tr
from myapps.ui.models.project_list_model import PROJECT_ID_MIME_TYPE

ALL_ITEM_ID = "__all__"


class CategorySidebar(QListWidget):
    filter_changed = Signal(str)  # ALL_ITEM_ID | UNCATEGORIZED_ID | category_id
    project_recategorized = Signal(str, str)  # project_name, category_label (for status bar)

    def __init__(self, project_manager: ProjectManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CategorySidebar")
        self._pm = project_manager
        self.setFrameShape(QListWidget.Shape.NoFrame)
        self.setAcceptDrops(True)

        self._refresh()
        self.currentItemChanged.connect(self._on_current_changed)

        event_bus.category_added.connect(self._refresh)
        event_bus.category_updated.connect(self._refresh)
        event_bus.category_removed.connect(self._refresh)
        event_bus.project_added.connect(self._refresh)
        event_bus.project_removed.connect(self._refresh)
        event_bus.project_updated.connect(self._refresh)

    def _refresh(self, *_args) -> None:
        previously_selected = self._current_filter_id()
        self.blockSignals(True)
        self.clear()

        all_item = QListWidgetItem(tr("sidebar.all", n=len(self._pm.list_projects())))
        all_item.setData(Qt.ItemDataRole.UserRole, ALL_ITEM_ID)
        self.addItem(all_item)

        for category in self._pm.list_categories():
            # category.name is user data, never translated - only the
            # "{name} ({n})" template is.
            count = len(self._pm.projects_in_category(category.id))
            display_name = f"{category.icon} {category.name}" if category.icon else category.name
            item = QListWidgetItem(tr("sidebar.category_count", name=display_name, n=count))
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self.addItem(item)

        uncategorized_count = len(self._pm.projects_in_category(None))
        uncategorized_item = QListWidgetItem(
            tr("sidebar.uncategorized_count", n=uncategorized_count)
        )
        uncategorized_item.setData(Qt.ItemDataRole.UserRole, UNCATEGORIZED_ID)
        self.addItem(uncategorized_item)

        self.blockSignals(False)
        self._select_filter_id(previously_selected or ALL_ITEM_ID)

    def _current_filter_id(self) -> str | None:
        item = self.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _select_filter_id(self, filter_id: str) -> None:
        for row in range(self.count()):
            item = self.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == filter_id:
                self.setCurrentItem(item)
                return
        if self.count():
            self.setCurrentRow(0)

    def _on_current_changed(self, current: QListWidgetItem, _previous) -> None:
        if current:
            self.filter_changed.emit(current.data(Qt.ItemDataRole.UserRole))

    # -- drag & drop (project -> category) --------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(PROJECT_ID_MIME_TYPE):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(PROJECT_ID_MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        if not event.mimeData().hasFormat(PROJECT_ID_MIME_TYPE):
            return
        target_item = self.itemAt(event.position().toPoint())
        project_id = bytes(event.mimeData().data(PROJECT_ID_MIME_TYPE)).decode("utf-8")
        if self._handle_drop(target_item, project_id):
            event.acceptProposedAction()

    def _handle_drop(self, target_item: QListWidgetItem | None, project_id: str) -> bool:
        """Applies the drop: replaces `project_id`'s categories with just the
        target category (or clears them, for "Uncategorized"). Separated from
        dropEvent() so it can be exercised directly in tests without
        constructing a real QDropEvent (fragile in PySide6 - event objects
        built in Python can crash when Qt's C++ side later reads them back).
        Returns True if the drop was handled.
        """
        if target_item is None:
            return False
        target_id = target_item.data(Qt.ItemDataRole.UserRole)
        if target_id == ALL_ITEM_ID:
            return False  # "All" isn't a real category to move into

        project = self._pm.get_project(project_id)
        if not project:
            return False

        if target_id == UNCATEGORIZED_ID:
            self._pm.set_categories(project_id, [])
            category_label = tr("sidebar.uncategorized")
        else:
            self._pm.set_categories(project_id, [target_id])
            category = self._pm.get_category(target_id)
            category_label = category.name if category else target_id

        self.project_recategorized.emit(project.name, category_label)
        return True
