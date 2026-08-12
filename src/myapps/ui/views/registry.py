"""Registry mapping a view-mode id to a factory that builds the widget for it.

Deliberately generic, no domain logic — mirrors `core/events.py`'s "just
plumbing" style. `main_window.py` registers the built-in list/grid modes at
startup; Phase 2's PluginManager registers plugin-contributed modes the same
way, through the exact same `register()` call, so this is a real
extensibility point rather than a hardcoded if/else.

Contract: any widget a factory returns must emit the same two signals
`ProjectListView` already does — `open_requested(str)` and
`context_menu_requested(str, QPoint)` — so `MainWindow` can wire it up
identically regardless of which mode it came from. This can't be enforced via
a typed Protocol because Qt Signals don't mix cleanly with ABCs/Protocols, so
it's a documented convention instead.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QWidget

from myapps.ui.models.project_list_model import ProjectListModel

ViewFactory = Callable[[ProjectListModel, QItemSelectionModel], QWidget]


@dataclass(frozen=True)
class ViewModeInfo:
    mode_id: str
    label: str
    factory: ViewFactory


class ViewRegistry:
    def __init__(self) -> None:
        self._modes: dict[str, ViewModeInfo] = {}

    def register(self, mode_id: str, label: str, factory: ViewFactory) -> None:
        self._modes[mode_id] = ViewModeInfo(mode_id, label, factory)

    def unregister(self, mode_id: str) -> None:
        self._modes.pop(mode_id, None)

    def get(self, mode_id: str) -> ViewModeInfo | None:
        return self._modes.get(mode_id)

    def list_modes(self) -> list[ViewModeInfo]:
        """Registration order (built-ins first, then plugin-contributed)."""
        return list(self._modes.values())


# Single shared instance for the whole app, same pattern as `core.events.event_bus`.
view_registry = ViewRegistry()
