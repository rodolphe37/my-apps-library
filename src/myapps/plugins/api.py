"""The plugin API surface: PluginBase (lifecycle hooks) and PluginContext
(the only object plugins receive - never raw app internals). Keeping
PluginContext as the sole surface is what makes a future real sandbox
retrofit-able without changing this contract.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtGui import QPixmap

from myapps.core.models import Project
from myapps.core.project_manager import ProjectManager
from myapps.core.store import load_json, save_json
from myapps.ui.views.registry import ViewFactory, ViewModeInfo


@dataclass(frozen=True)
class PluginMenuAction:
    label: str
    callback: Callable[[], None]
    enabled: bool = True


@dataclass(frozen=True)
class IconDef:
    """A single pickable icon: `glyph` is a short unicode string, typically
    one emoji (renders identically in light/dark - already color-neutral)
    or a plain symbol character (rendered in the app's current text color
    via the icon picker/list, so it's theme-aware for free either way - no
    image assets, no per-theme variants to ship)."""

    id: str
    glyph: str
    label: str = ""


@dataclass(frozen=True)
class IconPack:
    """A named, orderable collection of IconDef, shown as its own section
    in the icon picker (Categories → choose icon) alongside the built-in
    pack and any other enabled plugin's pack."""

    id: str
    label: str
    icons: list[IconDef] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectBadge:
    """A small overlay painted in the corner of a project's folder icon, in
    BOTH the built-in List and Grid views (not an opt-in alternate view -
    see contribute_views() for that) - e.g. a detected tech/language logo.

    `pixmap` should be small and roughly square (a higher-res source stays
    crisp on HiDPI - ProjectItemDelegate scales it down to the on-screen
    badge size, never up). `tooltip`, if non-empty, is appended to the
    folder icon's own tooltip text.

    Contributing plugin is responsible for its own caching - see
    contribute_project_badge()'s docstring: this is read on every repaint,
    so it must return near-instantly."""

    pixmap: QPixmap
    tooltip: str = ""


@dataclass(frozen=True)
class ProjectActionButton:
    """A small clickable button painted over a project's folder icon, in
    BOTH the built-in List and Grid views - the interactive counterpart to
    ProjectBadge (which is paint-only). Clipped to the icon's top-left
    corner (ProjectBadge already owns the bottom-right corner, and the pin
    star owns the tile's own top-right corner).

    `glyph` is a short unicode string, same convention as IconDef.glyph -
    typically one character/emoji, rendered centered inside the button.
    `tooltip`, if non-empty, is shown on hover. `on_click` is called with no
    arguments when the button is clicked - a plugin typically builds this as
    a closure over the `project` passed to contribute_project_action_button
    (e.g. `lambda: self._open_dialog(project)`).

    Like ProjectBadge, this is read on every repaint of that project's row/
    tile, so contribute_project_action_button() must return near-instantly -
    do any real work (detecting what the button should do) lazily, inside
    on_click, not while building this dataclass.

    If more than one enabled plugin contributes a button for the same
    project, the first one (load order) wins - same 'never crash, never
    stack unbounded UI' rule ProjectBadge follows."""

    glyph: str
    on_click: Callable[[], None]
    tooltip: str = ""


@dataclass(frozen=True)
class ThemePalette:
    """A named color scheme, selectable from Preferences → Theme alongside
    the built-in default. `light` and `dark` must each be a complete token
    dict - see ui/theme/tokens.py's TOKEN_KEYS for the exact keys expected
    and ui/theme/tokens.default_light_tokens()/default_dark_tokens() for a
    working example to copy. A palette missing either variant, or with an
    incomplete token dict, is rejected at collection time (falls back to
    the built-in default) rather than crashing the host."""

    id: str
    label: str
    light: dict[str, str]
    dark: dict[str, str]


class PluginBase:
    """Base class for all plugins. Every hook is optional and defaults to a
    no-op / empty list - a plugin only overrides what it needs. Do setup in
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

    def contribute_project_badge(self, project: Project) -> ProjectBadge | None:
        """Optional: a small logo/overlay painted on `project`'s folder icon
        in the real built-in List and Grid views - see ProjectBadge's
        docstring. Return None to contribute nothing for this project (the
        default).

        Called on every repaint of that project's row/tile, so it MUST
        return quickly - do any expensive work (filesystem scanning,
        network, ...) in a background thread the first time a project is
        seen, cache the result, and return None until it's ready. Once
        ready, emit `myapps.core.events.event_bus.project_updated(project.
        id)` from the plugin so the view picks the badge up on its next
        repaint - see finder-style-info's GetInfoDialog for the same
        background-thread-plus-signal pattern applied to a dialog instead
        of a delegate.

        If more than one enabled plugin contributes a badge for the same
        project, the first one (load order) wins - the rest are silently
        dropped, same 'never crash, never stack unbounded UI' spirit as the
        rest of this module."""
        return None

    def contribute_project_action_button(self, project: Project) -> ProjectActionButton | None:
        """Optional: a small clickable button painted on `project`'s folder
        icon in the real built-in List and Grid views - see
        ProjectActionButton's docstring. Return None to contribute nothing
        for this project (the default).

        Called on every repaint, same constraint as
        contribute_project_badge() - return quickly, and do any real work
        (e.g. detecting how to run this project) inside the button's
        on_click callback instead, not here."""
        return None

    def contribute_views(self) -> list[ViewModeInfo]:
        return []

    def contribute_translations(self) -> dict[str, dict[str, str]]:
        """Optional: {locale_code: {key: translated_string}}. A plugin can
        EITHER patch/add keys onto an existing locale (e.g. adding French
        strings for its own contributed menu action) OR introduce a wholly
        new locale code (e.g. 'de') - same dict shape either way. The
        reserved key 'meta.language_name' inside a new locale's dict is what
        makes that locale display with a proper name (e.g. 'Deutsch') in the
        Settings dropdown."""
        return {}

    def contribute_icon_packs(self) -> list[IconPack]:
        """Optional: named icon collections offered in the icon picker
        (Categories → choose icon), alongside the built-in pack."""
        return []

    def contribute_theme_palettes(self) -> list[ThemePalette]:
        """Optional: named color schemes offered in Preferences → Theme,
        alongside the built-in default. Each must supply both a light and a
        dark token dict - see ThemePalette's docstring."""
        return []


class PluginSettingsStore:
    """Per-plugin settings, persisted to `<storage_dir>/settings.json` via
    the existing atomic-write helpers in core/store.py. Deliberately does NOT
    touch AppSettings/settings.json - namespacing falls out for free from
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
    value - same underlying storage, two ergonomics.
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
