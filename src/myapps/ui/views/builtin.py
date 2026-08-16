"""Registers the two built-in view modes (list, grid) into a ViewRegistry.

Each factory builds its OWN ProjectItemDelegate instance - never share one
between the two views, since `display_mode` is mutable instance state and
both views coexist simultaneously inside MainWindow's QStackedWidget (hidden,
not destroyed).
"""

from __future__ import annotations

from PySide6.QtWidgets import QListView

from myapps.core.project_manager import ProjectManager
from myapps.i18n import tr
from myapps.plugins.manager import PluginManager
from myapps.ui.delegates.project_item_delegate import ProjectItemDelegate
from myapps.ui.views.project_list_view import ProjectListView
from myapps.ui.views.registry import ViewRegistry

LIST_MODE_ID = "list"
GRID_MODE_ID = "grid"


def register_builtin_views(
    registry: ViewRegistry,
    project_manager: ProjectManager,
    plugin_manager: PluginManager | None = None,
) -> None:
    """Re-runnable (called again on language change to re-translate the
    "List"/"Grid" labels) - registry.register() overwrites by mode_id.

    `plugin_manager` is optional (some callers/tests build a ViewRegistry
    without one) - the built-in views simply paint no project badges when
    it's None, same "degrades quietly" spirit as the rest of the plugin
    system."""
    registry.register(
        LIST_MODE_ID,
        tr("view_mode.list"),
        lambda m, s: _make_list_view(m, s, project_manager, plugin_manager),
    )
    registry.register(
        GRID_MODE_ID,
        tr("view_mode.grid"),
        lambda m, s: _make_grid_view(m, s, project_manager, plugin_manager),
    )


def _make_list_view(
    model, selection_model, project_manager: ProjectManager, plugin_manager: PluginManager | None
) -> ProjectListView:
    delegate = ProjectItemDelegate(project_manager, plugin_manager)
    delegate.display_mode = "row"
    view = ProjectListView(model, delegate, view_mode=QListView.ViewMode.ListMode)
    view.setSelectionModel(selection_model)
    return view


def _make_grid_view(
    model, selection_model, project_manager: ProjectManager, plugin_manager: PluginManager | None
) -> ProjectListView:
    delegate = ProjectItemDelegate(project_manager, plugin_manager)
    delegate.display_mode = "tile"
    view = ProjectListView(model, delegate, view_mode=QListView.ViewMode.IconMode)
    view.setSelectionModel(selection_model)
    return view
