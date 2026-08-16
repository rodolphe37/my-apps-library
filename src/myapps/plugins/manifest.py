"""PluginManifest: parsed and validated from a `plugin.toml` file.

Hand-rolled validation, not pydantic - matches the precedent already set in
`core/models.py` (plain dataclasses; strictness isolated to where it's
actually needed). This schema is ~9 flat scalar/list-of-str fields with no
nesting and no cross-field business rules beyond a regex and required-field
checks, so a new runtime dependency (that would also ship in the PyInstaller
bundle) isn't worth it just to validate a handful of strings once at load
time.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from myapps.utils.version_utils import parse_version

PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9_-]+$")

REQUIRED_STRING_FIELDS = ("id", "name", "version", "entry_point")


class ManifestError(ValueError):
    """Raised for any problem parsing or validating a plugin.toml. Aggregates
    every problem found into one message rather than failing on the first."""


@dataclass(frozen=True)
class PluginManifest:
    id: str
    name: str
    version: str
    entry_point: str  # "module:ClassName"
    description: str = ""
    author: str = ""
    license: str = ""
    min_app_version: str = "0.0.0"
    permissions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    # Advisory discoverability metadata for a translation plugin - e.g.
    # ["de"]. Not enforced: the runtime source of truth for what a plugin
    # actually translates is its loaded contribute_translations() return
    # value (same advisory relationship `permissions` already has to actual
    # behavior). Lets the UI show "Provides: German" without loading code.
    provides_locales: list[str] = field(default_factory=list)
    # Optional path to a logo image (PNG/SVG/JPEG/WEBP), relative to the
    # plugin's own folder - e.g. "icon.png". Not validated at parse time
    # (the file may not exist, may be unreadable, or may fail to decode -
    # none of that should ever block loading the plugin itself); see
    # `icon_path` below for the fail-open resolution used at display time.
    icon: str | None = None
    # Injected by the loader, not part of the TOML itself.
    source_dir: Path | None = None

    @property
    def icon_path(self) -> Path | None:
        """Resolves `icon` against `source_dir` and returns it only if the
        file actually exists - `None` in every other case (no `icon`
        declared, no `source_dir` yet, or a dangling/typo'd path), so a
        caller never needs its own existence check before using this."""
        if not self.icon or self.source_dir is None:
            return None
        candidate = (self.source_dir / self.icon).resolve()
        return candidate if candidate.is_file() else None


def parse_manifest(toml_path: Path) -> PluginManifest:
    """Parse and validate a plugin.toml file. Raises ManifestError with all
    problems aggregated into one message on any failure - never lets a raw
    tomllib exception escape."""
    try:
        with toml_path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"{toml_path}: invalid TOML ({exc})") from exc
    except OSError as exc:
        raise ManifestError(f"{toml_path}: could not read file ({exc})") from exc

    plugin_section = data.get("plugin")
    if not isinstance(plugin_section, dict):
        raise ManifestError(f"{toml_path}: missing [plugin] section")

    errors = _validate(plugin_section)
    if errors:
        raise ManifestError(f"{toml_path}: " + "; ".join(errors))

    return PluginManifest(
        id=plugin_section["id"],
        name=plugin_section["name"],
        version=str(plugin_section["version"]),
        entry_point=plugin_section["entry_point"],
        description=plugin_section.get("description", ""),
        author=plugin_section.get("author", ""),
        license=plugin_section.get("license", ""),
        min_app_version=str(plugin_section.get("min_app_version", "0.0.0")),
        permissions=list(plugin_section.get("permissions", [])),
        tags=list(plugin_section.get("tags", [])),
        provides_locales=list(plugin_section.get("provides_locales", [])),
        icon=plugin_section.get("icon") or None,
        source_dir=toml_path.parent,
    )


def _validate(section: dict) -> list[str]:
    errors: list[str] = []

    for field_name in REQUIRED_STRING_FIELDS:
        value = section.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"'{field_name}' is required and must be a non-empty string")

    icon = section.get("icon")
    if icon is not None and not isinstance(icon, str):
        errors.append("'icon' must be a string (a path relative to the plugin's own folder)")

    plugin_id = section.get("id")
    if isinstance(plugin_id, str) and plugin_id and not PLUGIN_ID_PATTERN.match(plugin_id):
        errors.append(
            f"'id' {plugin_id!r} must match {PLUGIN_ID_PATTERN.pattern} "
            "(lowercase letters, digits, '-', '_')"
        )

    entry_point = section.get("entry_point")
    if isinstance(entry_point, str) and entry_point and ":" not in entry_point:
        errors.append("'entry_point' must be of the form 'module:ClassName'")

    for list_field in ("permissions", "tags", "provides_locales"):
        value = section.get(list_field, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            errors.append(f"'{list_field}' must be a list of strings")

    return errors


def parse_min_app_version(version: str) -> tuple[int, ...]:
    """Thin, name-preserving wrapper around utils/version_utils.py's
    parse_version() - kept here too since it's this module's own public API
    (see tests/unit/test_plugin_manifest.py) and reads more naturally at
    call sites that are specifically about min_app_version."""
    return parse_version(version)
