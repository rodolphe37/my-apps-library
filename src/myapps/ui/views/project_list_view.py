"""A QListView using ProjectListModel and ProjectItemDelegate, usable in
either ListMode (row layout, MVP default) or IconMode (grid/tile layout,
Phase 2) via the `view_mode` constructor kwarg. Emits signals for the actions
main_window.py wires up, regardless of mode - see ui/views/registry.py's
module docstring for the contract this relies on.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QAbstractItemView, QListView, QStyleOptionViewItem

from myapps.ui.delegates.project_item_delegate import ProjectItemDelegate
from myapps.ui.models.project_list_model import ProjectIdRole


class ProjectListView(QListView):
    open_requested = Signal(str)  # project_id
    context_menu_requested = Signal(str, object)  # project_id, global QPoint
    # A plugin-contributed card button (api.ProjectActionButton) was
    # left-clicked - see mousePressEvent()'s hit-test against the delegate's
    # own action_button_rect().
    action_button_clicked = Signal(str)  # project_id
    # External folders dragged in from Finder/Explorer, dropped directly on
    # this view. Handled here (in both list and grid mode) rather than
    # relying on the drop bubbling up to MainWindow's own dragEnterEvent/
    # dropEvent - Qt's propagation of unhandled drag events from a nested
    # QAbstractItemView's viewport up to an ancestor widget isn't reliable
    # enough to depend on, so each view explicitly accepts and re-emits
    # external file drops itself instead.
    external_folders_dropped = Signal(list)  # list[str] of folder paths

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
        # Extended = click selects one, Ctrl/Cmd-click toggles individual
        # items, Shift-click selects a contiguous range - the standard
        # Finder/Explorer multi-select convention. Bulk actions (edit
        # categories, pin, remove) act on the whole selection; see
        # MainWindow._selected_project_ids().
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setMouseTracking(True)  # needed for the grid delegate's hover state

        # DragOnly governs INTERNAL item drag/drop only (dragging a project
        # onto a category in the sidebar - see ProjectListModel.mimeData());
        # it does not accept drops back onto this view. Re-enabled below via
        # setAcceptDrops(True) so the view can still separately accept
        # EXTERNAL file drops from Finder/Explorer (handled in the three
        # drag*/drop event overrides), without those two concerns conflicting.
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setAcceptDrops(True)

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

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        # A left click landing inside a plugin-contributed action button's
        # circle (see ProjectItemDelegate.action_button_rect()) fires that
        # instead of the normal QListView click handling (selection, drag
        # start) - the button and the rest of the row/tile are mutually
        # exclusive click targets.
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            index = self.indexAt(pos)
            # itemDelegate() with no args, not itemDelegate(index) - the
            # constructor always installs one shared delegate for every row
            # (see __init__), and the no-arg overload isn't deprecated.
            delegate = self.itemDelegate()
            if index.isValid() and isinstance(delegate, ProjectItemDelegate):
                # QAbstractItemView.viewOptions() was removed in Qt6 -
                # initViewItemOption() is its replacement (fills an option
                # in place rather than returning one).
                option = QStyleOptionViewItem()
                self.initViewItemOption(option)
                option.rect = self.visualRect(index)
                button_rect = delegate.action_button_rect(option, index)
                if button_rect is not None and button_rect.contains(pos):
                    project_id = index.data(ProjectIdRole)
                    if project_id:
                        self.action_button_clicked.emit(project_id)
                    return
        super().mousePressEvent(event)

    def _on_context_menu(self, pos) -> None:
        index = self.indexAt(pos)
        if not index.isValid():
            return
        project_id = index.data(ProjectIdRole)
        if project_id:
            self.context_menu_requested.emit(project_id, self.viewport().mapToGlobal(pos))

    # -- external (Finder/Explorer) drag & drop import ---------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        folders = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile() and Path(url.toLocalFile()).is_dir()
        ]
        if not folders:
            super().dropEvent(event)
            return
        event.acceptProposedAction()
        self.external_folders_dropped.emit(folders)
