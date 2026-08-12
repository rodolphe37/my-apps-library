"""QAbstractListModel wrapping ProjectManager's data.

This is the single source of truth for the list view; Phase 2's grid view is
designed to reuse this same model + a different delegate, rather than
duplicating data access.
"""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from myapps.core.events import event_bus
from myapps.core.models import Project
from myapps.core.project_manager import ProjectManager

# Custom roles, starting after Qt's reserved built-in roles.
ProjectIdRole = Qt.ItemDataRole.UserRole + 1
ProjectPathRole = Qt.ItemDataRole.UserRole + 2
CategoriesRole = Qt.ItemDataRole.UserRole + 3
EditorIdRole = Qt.ItemDataRole.UserRole + 4
PinnedRole = Qt.ItemDataRole.UserRole + 5
DescriptionRole = Qt.ItemDataRole.UserRole + 6


class ProjectListModel(QAbstractListModel):
    def __init__(self, project_manager: ProjectManager, parent=None) -> None:
        super().__init__(parent)
        self._pm = project_manager
        self._category_filter: str | None | object = _NO_FILTER
        self._search_text = ""
        self._projects: list[Project] = []
        self._refresh()

        event_bus.project_added.connect(self._on_data_changed)
        event_bus.project_removed.connect(self._on_data_changed)
        event_bus.project_updated.connect(self._on_data_changed)
        event_bus.category_removed.connect(self._on_data_changed)

    # -- filtering -----------------------------------------------------

    def set_category_filter(self, category_id: str | None) -> None:
        """`None` means the special 'Uncategorized' bucket; use `clear_filter()`
        for 'show everything'."""
        self._category_filter = category_id
        self._refresh()

    def clear_filter(self) -> None:
        self._category_filter = _NO_FILTER
        self._refresh()

    def set_search_text(self, text: str) -> None:
        self._search_text = text.strip().lower()
        self._refresh()

    # -- Qt model interface ----------------------------------------------

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is not None and parent.isValid():
            return 0
        return len(self._projects)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._projects)):
            return None
        project = self._projects[index.row()]

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return project.name
        if role == Qt.ItemDataRole.ToolTipRole:
            return project.path
        if role == ProjectIdRole:
            return project.id
        if role == ProjectPathRole:
            return project.path
        if role == CategoriesRole:
            return list(project.categories)
        if role == EditorIdRole:
            return project.preferred_editor_id
        if role == PinnedRole:
            return project.pinned
        if role == DescriptionRole:
            return project.description
        return None

    def roleNames(self) -> dict:  # noqa: N802
        return {
            Qt.ItemDataRole.DisplayRole: b"name",
            ProjectIdRole: b"projectId",
            ProjectPathRole: b"path",
            CategoriesRole: b"categories",
            EditorIdRole: b"editorId",
            PinnedRole: b"pinned",
            DescriptionRole: b"description",
        }

    def project_at(self, row: int) -> Project | None:
        if 0 <= row < len(self._projects):
            return self._projects[row]
        return None

    # -- internal ------------------------------------------------------

    def _on_data_changed(self, *_args) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self.beginResetModel()
        if self._category_filter is _NO_FILTER:
            projects = self._pm.list_projects()
        else:
            projects = self._pm.projects_in_category(self._category_filter)
        if self._search_text:
            projects = [p for p in projects if self._search_text in p.name.lower()]
        self._projects = projects
        self.endResetModel()


class _NoFilterSentinel:
    """Distinguishes 'no category filter' from 'filter = Uncategorized (None)'."""


_NO_FILTER = _NoFilterSentinel()
