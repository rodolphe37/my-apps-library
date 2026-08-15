"""Discovers plugin manifests without importing plugin code.

Two sources: the local plugins folder (plugin.toml files dropped in by the
user or by PluginManager.install_from_path), and Python entry_points (for
plugins pip-installed into the same environment - a secondary/advanced path,
since there's no real distribution flow yet; that's Phase 3's marketplace).
"""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from pathlib import Path

from myapps.plugins.manifest import ManifestError, PluginManifest, parse_manifest

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "myapps.plugins"


def discover_local(plugins_dir: Path) -> list[PluginManifest]:
    """plugin_dir/*/plugin.toml for each subfolder of `plugins_dir`. A broken
    manifest is logged and skipped - this never raises."""
    if not plugins_dir.exists():
        return []

    manifests: list[PluginManifest] = []
    for entry in sorted(plugins_dir.iterdir()):
        if not entry.is_dir():
            continue
        toml_path = entry / "plugin.toml"
        if not toml_path.exists():
            continue
        try:
            manifests.append(parse_manifest(toml_path))
        except ManifestError:
            logger.exception("Skipping invalid plugin manifest at %s", toml_path)
    return manifests


def discover_entry_points() -> list[str]:
    """Lists entry-point names only (group=myapps.plugins) - deliberately not
    hydrated into full PluginManifests here, since that would require
    importing plugin code, breaking the 'discover without importing'
    guarantee that matters for local/zip-sourced plugins. Full manifest +
    import happens together at PluginManager.load() time for this source too.
    Best-effort: never raises."""
    try:
        return [ep.name for ep in entry_points(group=ENTRY_POINT_GROUP)]
    except Exception:
        logger.exception("Failed to enumerate entry_points(group=%r)", ENTRY_POINT_GROUP)
        return []
