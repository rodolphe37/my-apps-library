"""macOS editor detection: CLI shims on PATH, then a bundled CLI inside the
.app package itself, then `open -a` as a last resort.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from myapps.editors.base import EditorInfo
from myapps.editors.catalog import CATALOG

APPLICATIONS_DIRS = [Path("/Applications"), Path.home() / "Applications"]

# VS Code and its Electron-based forks (Cursor, VSCodium, Insiders builds)
# all ship their own `code`-style CLI binary inside the .app bundle, at this
# relative path - the same binary that gets symlinked onto PATH when the
# user runs "Shell Command: Install 'code' command in PATH" from the command
# palette. Checking for it directly means launching still works reliably
# even if the user never ran that command.
_BUNDLED_CLI_RELATIVE_PATH = Path("Contents/Resources/app/bin")


def detect() -> list[EditorInfo]:
    found: list[EditorInfo] = []
    for entry in CATALOG:
        # 1. A CLI shim on PATH - most reliable, respects the user's own setup.
        cli_path = None
        for name in entry.cli_names:
            cli_path = shutil.which(name)
            if cli_path:
                break

        app_path = _find_app_bundle(entry.mac_app_names)

        # 2. A CLI binary bundled inside the .app itself, even if it was
        # never linked onto PATH.
        if not cli_path and app_path:
            cli_path = _find_bundled_cli(app_path, entry.cli_names)

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

        # 3. Last resort: `open -a`. Note this is NOT reliable for passing
        # `--args` to an app that's already running - macOS's `open` just
        # activates the existing instance and silently drops the new args
        # in that case. Only reached when no CLI binary could be found at
        # all (steps 1-2 above), which is now the uncommon case for the
        # Electron-based editors in this catalog.
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


def _find_bundled_cli(app_path: Path, cli_names: tuple[str, ...]) -> str | None:
    bin_dir = app_path / _BUNDLED_CLI_RELATIVE_PATH
    for name in cli_names:
        candidate = bin_dir / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None
