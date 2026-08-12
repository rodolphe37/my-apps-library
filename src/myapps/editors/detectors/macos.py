"""macOS editor detection: CLI shims on PATH, then /Applications bundles."""

from __future__ import annotations

import shutil
from pathlib import Path

from myapps.editors.base import EditorInfo
from myapps.editors.catalog import CATALOG

APPLICATIONS_DIRS = [Path("/Applications"), Path.home() / "Applications"]


def detect() -> list[EditorInfo]:
    found: list[EditorInfo] = []
    for entry in CATALOG:
        # Prefer a CLI shim if present — it's more reliable than `open -a`.
        cli_path = None
        for name in entry.cli_names:
            cli_path = shutil.which(name)
            if cli_path:
                break

        if cli_path:
            found.append(
                EditorInfo(
                    id=entry.id,
                    display_name=entry.display_name,
                    executable_path=cli_path,
                    kind="detected",
                    launch_strategy="cli",
                    launch_template=[cli_path, *entry.cli_open_args],
                )
            )
            continue

        # Fall back to an installed .app bundle via `open -a`.
        app_path = _find_app_bundle(entry.mac_app_names)
        if app_path:
            found.append(
                EditorInfo(
                    id=entry.id,
                    display_name=entry.display_name,
                    executable_path=str(app_path),
                    kind="detected",
                    launch_strategy="mac_open",
                    launch_template=["open", "-a", str(app_path), "--args", "{path}"],
                    app_bundle=str(app_path),
                )
            )
    return found


def _find_app_bundle(names: tuple[str, ...]) -> Path | None:
    for base in APPLICATIONS_DIRS:
        for name in names:
            candidate = base / (name if name.endswith(".app") else f"{name}.app")
            if candidate.exists():
                return candidate
    return None
