"""Builds the right-click context menu for a project row.

Core actions live here; Phase 2's PluginManager will append
`contribute_project_context_actions(project)` results after a separator,
without this module needing to change.

Rebuilt fresh on every right-click (no stored state), so its `tr()` calls
always reflect the currently active language with no retranslation plumbing
needed.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QMenu, QWidget

from myapps.core.models import Project
from myapps.i18n import tr


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
    menu.addAction(tr("context_menu.open"), on_open)
    menu.addAction(tr("context_menu.open_with"), on_open_with)
    menu.addAction(tr("context_menu.reveal"), on_reveal)
    menu.addSeparator()
    menu.addAction(
        tr("context_menu.unpin") if project.pinned else tr("context_menu.pin"), on_toggle_pin
    )
    menu.addAction(tr("context_menu.edit_categories"), on_edit_categories)
    menu.addAction(tr("context_menu.rename"), on_rename)
    menu.addSeparator()
    remove_action = menu.addAction(tr("context_menu.remove"), on_remove)
    remove_action.setToolTip(tr("context_menu.remove_tooltip"))
    return menu
