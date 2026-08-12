"""A QListView using ProjectListModel and ProjectItemDelegate, usable in
either ListMode (row layout, MVP default) or IconMode (grid/tile layout,
Phase 2) via the `view_mode` constructor kwarg. Emits signals for the actions
main_window.py wires up, regardless of mode — see ui/views/registry.py's
module docstring for the contract this relies on.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QListView

from myapps.ui.delegates.project_item_delegate import ProjectItemDelegate
from myapps.ui.models.project_list_model import ProjectIdRole


class ProjectListView(QListView):
    open_requested = Signal(str)  # project_id
    context_menu_requested = Signal(str, object)  # project_id, global QPoint

    def __init__(
        self,
        model,
        delegate: ProjectItemDelegate,
        parent=None,
        *,
        view_mode: QListView.ViewMode = QListView.ViewMode.ListMode,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectListView")
        self.setModel(model)
        self.setItemDelegate(delegate)
        self.setViewMode(view_mode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setMouseTracking(True)  # needed for the grid delegate's hover state

        if view_mode == QListView.ViewMode.IconMode:
            self.setFlow(QListView.Flow.LeftToRight)
            self.setWrapping(True)
            self.setSpacing(8)
        else:
            self.setSpacing(2)

        self.doubleClicked.connect(self._on_double_clicked)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _on_double_clicked(self, index) -> None:
        project_id = index.data(ProjectIdRole)
        if project_id:
            self.open_requested.emit(project_id)

    def _on_context_menu(self, pos) -> None:
        index = self.indexAt(pos)
        if not index.isValid():
            return
        project_id = index.data(ProjectIdRole)
        if project_id:
            self.context_menu_requested.emit(project_id, self.viewport().mapToGlobal(pos))
