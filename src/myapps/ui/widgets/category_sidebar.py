"""Left sidebar: All / Uncategorized / each category, for filtering the
project list. Emits `category_selected(category_id_or_None)`; a sentinel
string "__all__" is translated to None-with-no-filter by main_window.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from myapps.constants import UNCATEGORIZED_ID
from myapps.core.events import event_bus
from myapps.core.project_manager import ProjectManager

ALL_ITEM_ID = "__all__"


class CategorySidebar(QListWidget):
    filter_changed = Signal(str)  # ALL_ITEM_ID | UNCATEGORIZED_ID | category_id

    def __init__(self, project_manager: ProjectManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CategorySidebar")
        self._pm = project_manager
        self.setFrameShape(QListWidget.Shape.NoFrame)

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

        all_item = QListWidgetItem(f"All ({len(self._pm.list_projects())})")
        all_item.setData(Qt.ItemDataRole.UserRole, ALL_ITEM_ID)
        self.addItem(all_item)

        for category in self._pm.list_categories():
            count = len(self._pm.projects_in_category(category.id))
            item = QListWidgetItem(f"{category.name} ({count})")
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self.addItem(item)

        uncategorized_count = len(self._pm.projects_in_category(None))
        uncategorized_item = QListWidgetItem(f"Uncategorized ({uncategorized_count})")
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
