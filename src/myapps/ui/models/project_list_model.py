"""QAbstractListModel wrapping ProjectManager's data.

This is the single source of truth for the list view; Phase 2's grid view is
designed to reuse this same model + a different delegate, rather than
duplicating data access.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QAbstractListModel, QMimeData, QModelIndex, Qt

from myapps.core.events import event_bus
from myapps.core.models import Project
from myapps.core.project_manager import ProjectManager
from myapps.utils.fs_utils import directory_size

SORT_KEYS = ("name", "created_at", "modified_at", "size")

# Custom roles, starting after Qt's reserved built-in roles.
ProjectIdRole = Qt.ItemDataRole.UserRole + 1
ProjectPathRole = Qt.ItemDataRole.UserRole + 2
CategoriesRole = Qt.ItemDataRole.UserRole + 3
EditorIdRole = Qt.ItemDataRole.UserRole + 4
PinnedRole = Qt.ItemDataRole.UserRole + 5
DescriptionRole = Qt.ItemDataRole.UserRole + 6
IconRole = Qt.ItemDataRole.UserRole + 7

# Drag payload: a single project id, utf-8 encoded. Used to drag a project
# from the list/grid view onto a category in the sidebar (see
# ui/widgets/category_sidebar.py's dropEvent).
PROJECT_ID_MIME_TYPE = "application/x-myapps-project-id"


class ProjectListModel(QAbstractListModel):
    def __init__(self, project_manager: ProjectManager, parent=None) -> None:
        super().__init__(parent)
        self._pm = project_manager
        self._category_filter: str | None | object = _NO_FILTER
        self._search_text = ""
        self._sort_key = "name"
        self._sort_direction = "asc"
        # In-memory only, keyed by project id — populated lazily the first
        # time sort_key == "size" is actually used, never persisted or
        # proactively invalidated (a project's on-disk size changing while
        # the app is running without a restart is an acceptable staleness
        # tradeoff here, same as elsewhere in this codebase).
        self._size_cache: dict[str, int] = {}
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

    # -- sorting ---------------------------------------------------------

    def set_sort(self, key: str, direction: str) -> None:
        """`key` is one of SORT_KEYS, `direction` is "asc"/"desc". An
        unrecognized key/direction falls back to name/asc rather than
        raising — the persisted value could in principle come from an
        older/newer settings.json."""
        self._sort_key = key if key in SORT_KEYS else "name"
        self._sort_direction = direction if direction in ("asc", "desc") else "asc"
        self._refresh()

    def _project_size(self, project: Project) -> int:
        cached = self._size_cache.get(project.id)
        if cached is None:
            cached = directory_size(project.path)
            self._size_cache[project.id] = cached
        return cached

    def _sort_value(self, project: Project):
        if self._sort_key == "name":
            return project.name.lower()
        if self._sort_key == "created_at":
            return project.created_at or ""
        if self._sort_key == "modified_at":
            try:
                return os.stat(project.path).st_mtime
            except OSError:
                return 0
        if self._sort_key == "size":
            return self._project_size(project)
        return project.name.lower()

    def _sort_projects(self, projects: list[Project]) -> list[Project]:
        # Two stable passes rather than one tuple-key sort: pinned projects
        # must stay a floated-to-top tier no matter which direction is
        # chosen (an outer key that never reverses), while the user's sort
        # key/direction only governs ordering *within* each tier (an inner
        # key that does reverse). Sorting by the inner key first, then
        # stably by the outer key, composes the two correctly — a single
        # `sorted(key=(not pinned, value), reverse=...)` would incorrectly
        # flip the pinned tier too whenever direction == "desc".
        by_value = sorted(projects, key=self._sort_value, reverse=self._sort_direction == "desc")
        return sorted(by_value, key=lambda p: not p.pinned)

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
        if role == IconRole:
            return project.icon
        return None

    def roleNames(self) -> dict:  # noqa: N802
        return {
            Qt.ItemDataRole.DisplayRole: b"name",
            ProjectIdRole: b"projectId",
            ProjectPathRole: b"path",
            CategoriesRole: b"categories",
            EditorIdRole: b"editorId",
            PinnedRole: b"pinned",
            IconRole: b"icon",
            DescriptionRole: b"description",
        }

    def project_at(self, row: int) -> Project | None:
        if 0 <= row < len(self._projects):
            return self._projects[row]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:  # noqa: N802
        base = super().flags(index)
        if index.isValid():
            return base | Qt.ItemFlag.ItemIsDragEnabled
        return base

    def mimeTypes(self) -> list[str]:  # noqa: N802
        return [PROJECT_ID_MIME_TYPE]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:  # noqa: N802
        mime = QMimeData()
        if indexes:
            project_id = indexes[0].data(ProjectIdRole) or ""
            mime.setData(PROJECT_ID_MIME_TYPE, project_id.encode("utf-8"))
        return mime

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
        self._projects = self._sort_projects(projects)
        self.endResetModel()


class _NoFilterSentinel:
    """Distinguishes 'no category filter' from 'filter = Uncategorized (None)'."""


_NO_FILTER = _NoFilterSentinel()
