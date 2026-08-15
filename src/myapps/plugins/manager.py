"""PluginManager: discover, load, enable/disable, install, and dispatch to
plugins. Every call into plugin code is isolated in try/except so one bad
plugin can never crash the host or block dispatch to the others.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import shutil
import sys
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from myapps.constants import VERSION
from myapps.core.events import event_bus
from myapps.core.models import Project
from myapps.core.project_manager import ProjectManager
from myapps.core.store import load_json, save_json
from myapps.paths import plugins_dir as default_plugins_dir
from myapps.plugins.api import (
    IconPack,
    PluginBase,
    PluginContext,
    PluginMenuAction,
    PluginSettingsStore,
    PluginUIRegistrar,
    ThemePalette,
)
from myapps.plugins.loader import discover_local
from myapps.plugins.manifest import (
    ManifestError,
    PluginManifest,
    parse_manifest,
    parse_min_app_version,
)
from myapps.ui.theme.tokens import validate_tokens
from myapps.ui.views.registry import ViewModeInfo

logger = logging.getLogger(__name__)

INSTALLED_FILE_NAME = "installed.json"


class PluginLoadState(Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    instance: PluginBase | None
    state: PluginLoadState
    error: str | None = None


@dataclass
class InstalledPluginRecord:
    plugin_id: str
    version: str
    source: str  # "local" | "entry_point"
    install_path: str | None
    enabled: bool
    installed_at: str

    def to_dict(self) -> dict:
        return {
            "plugin_id": self.plugin_id,
            "version": self.version,
            "source": self.source,
            "install_path": self.install_path,
            "enabled": self.enabled,
            "installed_at": self.installed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> InstalledPluginRecord:
        return cls(
            plugin_id=data["plugin_id"],
            version=data.get("version", "0.0.0"),
            source=data.get("source", "local"),
            install_path=data.get("install_path"),
            enabled=data.get("enabled", False),
            installed_at=data.get("installed_at", _now_iso()),
        )


class PluginInstallError(Exception):
    """Raised by install_from_path() — no partial state is left behind."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class PluginManager:
    def __init__(
        self,
        project_manager: ProjectManager,
        plugins_dir: Path | None = None,
        installed_file: Path | None = None,
    ) -> None:
        self._pm = project_manager
        self._plugins_dir = plugins_dir or default_plugins_dir()
        self._installed_file = installed_file or (self._plugins_dir / INSTALLED_FILE_NAME)
        self._installed: dict[str, InstalledPluginRecord] = self._load_installed()
        self._loaded: dict[str, LoadedPlugin] = {}
        self._registrars: dict[str, PluginUIRegistrar] = {}

        event_bus.project_added.connect(self.dispatch_project_added)
        event_bus.project_removed.connect(self.dispatch_project_removed)
        event_bus.project_opened.connect(self.dispatch_project_opened)

    # -- persistence -----------------------------------------------------

    def _load_installed(self) -> dict[str, InstalledPluginRecord]:
        data = load_json(self._installed_file, default={"plugins": []})
        return {
            r["plugin_id"]: InstalledPluginRecord.from_dict(r) for r in data.get("plugins", [])
        }

    def _save_installed(self) -> None:
        save_json(
            self._installed_file,
            {"plugins": [r.to_dict() for r in self._installed.values()]},
        )

    # -- discovery & loading -----------------------------------------------

    def discover(self) -> list[PluginManifest]:
        return discover_local(self._plugins_dir)

    def load_all_enabled(self) -> None:
        """Call once at app startup: discover local manifests and load every
        one whose installed.json record has enabled=True (or that has no
        record yet and is being tracked for the first time as disabled)."""
        for manifest in self.discover():
            record = self._installed.get(manifest.id)
            if record is None:
                # Seen for the first time (e.g. dropped into plugins_dir by
                # hand) — register as installed-but-disabled, don't auto-run.
                record = InstalledPluginRecord(
                    plugin_id=manifest.id,
                    version=manifest.version,
                    source="local",
                    install_path=str(manifest.source_dir) if manifest.source_dir else None,
                    enabled=False,
                    installed_at=_now_iso(),
                )
                self._installed[manifest.id] = record
                self._save_installed()
            if record.enabled:
                self.load(manifest)
            else:
                self._loaded[manifest.id] = LoadedPlugin(manifest, None, PluginLoadState.DISABLED)

    def load(self, manifest: PluginManifest) -> LoadedPlugin:
        """Dynamic import + instantiate + on_load(ctx). Never raises — a
        failure is captured as state=FAILED with the error message."""
        try:
            min_version = parse_min_app_version(manifest.min_app_version)
            current_version = parse_min_app_version(VERSION)
            if min_version > current_version:
                raise ManifestError(
                    f"requires app version >= {manifest.min_app_version}, running {VERSION}"
                )

            module_name, _, class_name = manifest.entry_point.partition(":")
            if not module_name or not class_name:
                raise ManifestError(f"invalid entry_point {manifest.entry_point!r}")

            module = self._import_plugin_module(manifest, module_name)
            plugin_class = getattr(module, class_name)
            instance: PluginBase = plugin_class()

            storage_dir = self._plugins_dir / manifest.id / "storage"
            storage_dir.mkdir(parents=True, exist_ok=True)
            registrar = PluginUIRegistrar()
            self._registrars[manifest.id] = registrar
            ctx = PluginContext(
                plugin_id=manifest.id,
                projects=self._pm,
                settings=PluginSettingsStore(storage_dir),
                ui=registrar,
                storage_dir=storage_dir,
            )
            instance.on_load(ctx)

            loaded = LoadedPlugin(manifest, instance, PluginLoadState.LOADED)
            self._loaded[manifest.id] = loaded
            return loaded
        except Exception as exc:
            logger.exception("Failed to load plugin %r", manifest.id)
            loaded = LoadedPlugin(manifest, None, PluginLoadState.FAILED, error=str(exc))
            self._loaded[manifest.id] = loaded
            return loaded

    @staticmethod
    def _import_plugin_module(manifest: PluginManifest, module_name: str):
        """Imports the plugin's module directly from its source_dir via
        importlib.util.spec_from_file_location, under a name namespaced by
        plugin id (`myapps_plugin_<id>.<module_name>`) rather than the bare
        module name. Two different plugins very commonly both name their
        entry file `plugin.py` (it's the convention this project's own
        examples use) — importing under the bare name would collide in
        sys.modules, silently returning the wrong plugin's module to the
        second loader. Entry_point-sourced plugins (no source_dir) are
        already importable normally via the standard mechanism."""
        if manifest.source_dir is None:
            return importlib.import_module(module_name)

        file_candidate = manifest.source_dir / f"{module_name}.py"
        pkg_candidate = manifest.source_dir / module_name / "__init__.py"
        if file_candidate.exists():
            source_file = file_candidate
        elif pkg_candidate.exists():
            source_file = pkg_candidate
        else:
            raise ManifestError(
                f"entry_point module {module_name!r} not found in {manifest.source_dir}"
            )

        unique_name = f"myapps_plugin_{manifest.id}.{module_name}"
        spec = importlib.util.spec_from_file_location(unique_name, source_file)
        if spec is None or spec.loader is None:
            raise ManifestError(f"could not load module {module_name!r} from {source_file}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        spec.loader.exec_module(module)
        return module

    # -- enable / disable ----------------------------------------------

    def enable(self, plugin_id: str) -> None:
        record = self._installed.get(plugin_id)
        if record is None:
            logger.error("Cannot enable unknown plugin %r", plugin_id)
            return
        record.enabled = True
        self._save_installed()
        manifest = self._manifest_for(plugin_id)
        if manifest:
            self.load(manifest)
        event_bus.plugins_changed.emit()

    def disable(self, plugin_id: str) -> None:
        """MVP disable = stop dispatch + drop from collect_*(). Does not
        truly unimport the module (Python has no clean unimport)."""
        record = self._installed.get(plugin_id)
        if record is None:
            return
        loaded = self._loaded.get(plugin_id)
        if loaded and loaded.instance is not None:
            try:
                loaded.instance.on_unload()
            except Exception:
                logger.exception("Plugin %r raised in on_unload()", plugin_id)
        record.enabled = False
        self._save_installed()
        if loaded:
            loaded.state = PluginLoadState.DISABLED
            loaded.instance = None
        event_bus.plugins_changed.emit()

    def _manifest_for(self, plugin_id: str) -> PluginManifest | None:
        for manifest in self.discover():
            if manifest.id == plugin_id:
                return manifest
        return None

    # -- install / uninstall -------------------------------------------

    def install_from_path(self, source_path: Path) -> PluginManifest:
        """Local zip or folder only — no networking. This is exactly the
        function Phase 3's marketplace client will call later after
        resolving a URL to a local download."""
        source_path = Path(source_path)
        if not source_path.exists():
            raise PluginInstallError(f"{source_path} does not exist")

        with tempfile.TemporaryDirectory(prefix="myapps-plugin-extract-") as scratch:
            scratch_path = Path(scratch)
            if source_path.is_file() and source_path.suffix == ".zip":
                try:
                    with zipfile.ZipFile(source_path) as zf:
                        zf.extractall(scratch_path)
                except zipfile.BadZipFile as exc:
                    raise PluginInstallError(f"{source_path} is not a valid zip file") from exc
                extracted_root = _find_manifest_root(scratch_path)
            elif source_path.is_dir():
                extracted_root = source_path if (source_path / "plugin.toml").exists() else None
            else:
                raise PluginInstallError(f"{source_path} is not a .zip file or a folder")

            if extracted_root is None:
                raise PluginInstallError("No plugin.toml found in the provided source")

            try:
                manifest = parse_manifest(extracted_root / "plugin.toml")
            except ManifestError as exc:
                raise PluginInstallError(str(exc)) from exc

            if manifest.id in self._installed:
                raise PluginInstallError(f"Plugin {manifest.id!r} is already installed")

            min_version = parse_min_app_version(manifest.min_app_version)
            if min_version > parse_min_app_version(VERSION):
                raise PluginInstallError(
                    f"Plugin {manifest.id!r} requires app version >= "
                    f"{manifest.min_app_version}, running {VERSION}"
                )

            final_dest = self._plugins_dir / manifest.id
            self._plugins_dir.mkdir(parents=True, exist_ok=True)
            tmp_dest = self._plugins_dir / f".tmp-{manifest.id}-{uuid.uuid4().hex}"
            shutil.copytree(extracted_root, tmp_dest)
            try:
                tmp_dest.replace(final_dest)  # directory-level atomic rename
            except OSError:
                shutil.rmtree(tmp_dest, ignore_errors=True)
                raise

        self._installed[manifest.id] = InstalledPluginRecord(
            plugin_id=manifest.id,
            version=manifest.version,
            source="local",
            install_path=str(final_dest),
            enabled=False,
            installed_at=_now_iso(),
        )
        self._save_installed()
        event_bus.plugins_changed.emit()
        return manifest

    def uninstall(self, plugin_id: str) -> None:
        record = self._installed.pop(plugin_id, None)
        if record is None:
            return
        self._loaded.pop(plugin_id, None)
        self._registrars.pop(plugin_id, None)
        self._save_installed()
        if record.install_path:
            shutil.rmtree(record.install_path, ignore_errors=True)
        event_bus.plugins_changed.emit()

    def installed_plugins(self) -> list[LoadedPlugin]:
        result = []
        manifests_by_id = {m.id: m for m in self.discover()}
        for plugin_id, record in self._installed.items():
            loaded = self._loaded.get(plugin_id)
            if loaded:
                result.append(loaded)
            else:
                manifest = manifests_by_id.get(plugin_id)
                if manifest:
                    state = PluginLoadState.LOADED if record.enabled else PluginLoadState.DISABLED
                    result.append(LoadedPlugin(manifest, None, state))
        return result

    # -- push dispatch (event_bus-driven) -----------------------------

    def dispatch_project_added(self, project_id: str) -> None:
        self._dispatch_each("on_project_added", lambda p: p.on_project_added(project_id))

    def dispatch_project_removed(self, project_id: str) -> None:
        self._dispatch_each("on_project_removed", lambda p: p.on_project_removed(project_id))

    def dispatch_project_opened(self, project_id: str, editor_id: str) -> None:
        self._dispatch_each(
            "on_project_opened", lambda p: p.on_project_opened(project_id, editor_id)
        )

    def _dispatch_each(self, hook_name: str, call) -> None:
        for plugin_id, loaded in self._loaded.items():
            if loaded.state != PluginLoadState.LOADED or loaded.instance is None:
                continue
            try:
                call(loaded.instance)
            except Exception:
                logger.exception("Plugin %r raised in %s()", plugin_id, hook_name)

    # -- pull collection (UI-build-time) --------------------------------

    def collect_menu_actions(self) -> list[PluginMenuAction]:
        actions: list[PluginMenuAction] = []
        for plugin_id, loaded in self._active_plugins():
            actions.extend(self._safe_call(plugin_id, loaded.instance.contribute_menu_actions, []))
            registrar = self._registrars.get(plugin_id)
            if registrar:
                actions.extend(registrar.menu_actions)
        return actions

    def collect_project_context_actions(self, project: Project) -> list[PluginMenuAction]:
        actions: list[PluginMenuAction] = []
        for plugin_id, loaded in self._active_plugins():
            actions.extend(
                self._safe_call(
                    plugin_id,
                    lambda inst=loaded.instance: inst.contribute_project_context_actions(project),
                    [],
                )
            )
            registrar = self._registrars.get(plugin_id)
            if registrar:
                for factory in registrar.project_action_factories:
                    actions.append(factory(project))
        return actions

    def collect_views(self) -> list[ViewModeInfo]:
        views: list[ViewModeInfo] = []
        for plugin_id, loaded in self._active_plugins():
            views.extend(self._safe_call(plugin_id, loaded.instance.contribute_views, []))
            registrar = self._registrars.get(plugin_id)
            if registrar:
                views.extend(registrar.views)
        return views

    def collect_translations(self) -> dict[str, dict[str, str]]:
        """Merges contribute_translations() from every LOADED+enabled
        plugin, locale-by-locale, key-by-key, in dict-iteration (i.e.
        load/enable) order. A later plugin's key wins over an earlier
        plugin's key for the same (locale, key) pair — same 'last writer
        wins, never crash' spirit as the rest of this module."""
        merged: dict[str, dict[str, str]] = {}
        for plugin_id, loaded in self._active_plugins():
            contributed = self._safe_call(plugin_id, loaded.instance.contribute_translations, {})
            for locale, entries in contributed.items():
                if not isinstance(entries, dict):
                    logger.warning(
                        "Plugin %r contributed non-dict translations for %r", plugin_id, locale
                    )
                    continue
                merged.setdefault(locale, {}).update(entries)
        return merged

    def collect_icon_packs(self) -> list[IconPack]:
        """Concatenates contribute_icon_packs() from every LOADED+enabled
        plugin, in load order. A plugin returning something other than a
        list of IconPack contributes nothing rather than crashing the
        picker."""
        packs: list[IconPack] = []
        for plugin_id, loaded in self._active_plugins():
            contributed = self._safe_call(plugin_id, loaded.instance.contribute_icon_packs, [])
            for pack in contributed:
                if not isinstance(pack, IconPack):
                    logger.warning("Plugin %r contributed a non-IconPack icon pack", plugin_id)
                    continue
                packs.append(pack)
        return packs

    def collect_theme_palettes(self) -> list[ThemePalette]:
        """Concatenates contribute_theme_palettes() from every LOADED+
        enabled plugin, in load order. A palette missing a complete light
        or dark token dict is dropped (logged, not raised) rather than
        letting a malformed palette reach ThemeManager and crash the
        stylesheet template substitution."""
        palettes: list[ThemePalette] = []
        for plugin_id, loaded in self._active_plugins():
            contributed = self._safe_call(plugin_id, loaded.instance.contribute_theme_palettes, [])
            for palette in contributed:
                if not isinstance(palette, ThemePalette):
                    logger.warning("Plugin %r contributed a non-ThemePalette palette", plugin_id)
                    continue
                light_problems = validate_tokens(palette.light)
                dark_problems = validate_tokens(palette.dark)
                if light_problems or dark_problems:
                    logger.warning(
                        "Plugin %r's palette %r has incomplete tokens "
                        "(light: %s, dark: %s), skipping",
                        plugin_id,
                        palette.id,
                        light_problems,
                        dark_problems,
                    )
                    continue
                palettes.append(palette)
        return palettes

    def _active_plugins(self):
        return [
            (pid, loaded)
            for pid, loaded in self._loaded.items()
            if loaded.state == PluginLoadState.LOADED and loaded.instance is not None
        ]

    def _safe_call(self, plugin_id: str, func, default):
        try:
            return func()
        except Exception:
            logger.exception("Plugin %r raised while collecting contributions", plugin_id)
            return default


def _find_manifest_root(scratch_path: Path) -> Path | None:
    """A zip may contain plugin.toml at its root, or inside a single wrapper
    folder (common when zipping a directory). Check both."""
    if (scratch_path / "plugin.toml").exists():
        return scratch_path
    children = list(scratch_path.iterdir())
    if len(children) == 1 and children[0].is_dir() and (children[0] / "plugin.toml").exists():
        return children[0]
    return None
