"""The plugin API surface: PluginBase (lifecycle hooks) and PluginContext
(the only object plugins receive — never raw app internals). Keeping
PluginContext as the sole surface is what makes a future real sandbox
retrofit-able without changing this contract.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from myapps.core.models import Project
from myapps.core.project_manager import ProjectManager
from myapps.core.store import load_json, save_json
from myapps.ui.views.registry import ViewFactory, ViewModeInfo


@dataclass(frozen=True)
class PluginMenuAction:
    label: str
    callback: Callable[[], None]
    enabled: bool = True


class PluginBase:
    """Base class for all plugins. Every hook is optional and defaults to a
    no-op / empty list — a plugin only overrides what it needs. Do setup in
    `on_load()`, not `__init__` (PluginManager instantiates with no args).
    """

    def on_load(self, ctx: PluginContext) -> None:
        """Called once, right after instantiation. Do setup here."""

    def on_unload(self) -> None:
        """Called before the plugin is disabled/uninstalled."""

    def on_project_added(self, project_id: str) -> None: ...

    def on_project_removed(self, project_id: str) -> None: ...

    def on_project_opened(self, project_id: str, editor_id: str) -> None: ...

    def contribute_menu_actions(self) -> list[PluginMenuAction]:
        return []

    def contribute_project_context_actions(self, project: Project) -> list[PluginMenuAction]:
        return []

    def contribute_views(self) -> list[ViewModeInfo]:
        return []


class PluginSettingsStore:
    """Per-plugin settings, persisted to `<storage_dir>/settings.json` via
    the existing atomic-write helpers in core/store.py. Deliberately does NOT
    touch AppSettings/settings.json — namespacing falls out for free from
    each plugin having its own storage_dir, no core schema change needed.
    """

    def __init__(self, storage_dir: Path) -> None:
        self._path = storage_dir / "settings.json"
        self._data = load_json(self._path, default={})

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        save_json(self._path, self._data)


class PluginUIRegistrar:
    """Imperative alternative to the `contribute_*()` return-value pattern,
    for plugins that want to add UI dynamically after on_load rather than
    declaratively. Internally appends to buffers that PluginManager's
    collect_*() methods read alongside each plugin's contribute_*() return
    value — same underlying storage, two ergonomics.
    """

    def __init__(self) -> None:
        self.menu_actions: list[PluginMenuAction] = []
        self.project_action_factories: list[Callable[[Project], PluginMenuAction]] = []
        self.views: list[ViewModeInfo] = []

    def register_menu_action(
        self, label: str, callback: Callable[[], None], *, enabled: bool = True
    ) -> None:
        self.menu_actions.append(PluginMenuAction(label, callback, enabled))

    def register_project_action(
        self, label: str, callback: Callable[[Project], None], *, enabled: bool = True
    ) -> None:
        self.project_action_factories.append(
            lambda project: PluginMenuAction(label, lambda: callback(project), enabled)
        )

    def register_view(self, mode_id: str, label: str, factory: ViewFactory) -> None:
        self.views.append(ViewModeInfo(mode_id, label, factory))


@dataclass
class PluginContext:
    plugin_id: str
    projects: ProjectManager
    settings: PluginSettingsStore
    ui: PluginUIRegistrar
    storage_dir: Path
    logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(f"myapps.plugins.{self.plugin_id}")
