"""Builds the right-click context menu for a project row.

Core actions live here; Phase 2's PluginManager will append
`contribute_project_context_actions(project)` results after a separator,
without this module needing to change.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QMenu, QWidget

from myapps.core.models import Project


def build_project_context_menu(
    project: Project,
    parent: QWidget,
    *,
    on_open: Callable[[], None],
    on_open_with: Callable[[], None],
    on_reveal: Callable[[], None],
    on_toggle_pin: Callable[[], None],
    on_edit_categories: Callable[[], None],
    on_rename: Callable[[], None],
    on_remove: Callable[[], None],
) -> QMenu:
    menu = QMenu(parent)
    menu.addAction("Open in Editor", on_open)
    menu.addAction("Open With…", on_open_with)
    menu.addAction("Show in Finder/Explorer", on_reveal)
    menu.addSeparator()
    menu.addAction("Unpin" if project.pinned else "Pin", on_toggle_pin)
    menu.addAction("Edit Categories…", on_edit_categories)
    menu.addAction("Rename…", on_rename)
    menu.addSeparator()
    remove_action = menu.addAction("Remove from Library…", on_remove)
    remove_action.setToolTip("Only removes the reference — your files are untouched")
    return menu
