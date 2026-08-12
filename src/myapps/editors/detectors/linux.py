"""Linux editor detection: PATH, .desktop files, and flatpak/snap listings."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from myapps.editors.base import EditorInfo
from myapps.editors.catalog import CATALOG

DESKTOP_DIRS = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
    Path.home() / ".local/share/applications",
]


def detect() -> list[EditorInfo]:
    found: list[EditorInfo] = []
    desktop_execs = _desktop_file_execs()
    flatpak_ids = _flatpak_app_ids()

    for entry in CATALOG:
        exe_path: str | None = None

        # 1. PATH
        for cli_name in entry.cli_names:
            candidate = shutil.which(cli_name)
            if candidate:
                exe_path = candidate
                break

        # 2. .desktop file Exec= line, matched by cli name appearing in the command
        if not exe_path:
            for cli_name in entry.cli_names:
                cmd = desktop_execs.get(cli_name.lower())
                if cmd:
                    exe_path = cmd
                    break

        # 3. Flatpak app id -> launch via `flatpak run <id>`
        if not exe_path and entry.linux_desktop_ids:
            matched_app_id = next(
                (aid for aid in entry.linux_desktop_ids if aid in flatpak_ids), None
            )
            if matched_app_id:
                found.append(
                    EditorInfo(
                        id=entry.id,
                        display_name=entry.display_name,
                        executable_path=f"flatpak run {matched_app_id}",
                        kind="detected",
                        launch_strategy="cli",
                        launch_template=["flatpak", "run", matched_app_id, "{path}"],
                    )
                )
                continue

        if exe_path:
            found.append(
                EditorInfo(
                    id=entry.id,
                    display_name=entry.display_name,
                    executable_path=exe_path,
                    kind="detected",
                    launch_strategy="cli",
                    launch_template=[exe_path, *entry.cli_open_args],
                )
            )
    return found


def _desktop_file_execs() -> dict[str, str]:
    """Best-effort map of lowercase binary-name -> resolved executable path,
    parsed from `Exec=` lines in .desktop files."""
    result: dict[str, str] = {}
    for base in DESKTOP_DIRS:
        if not base.exists():
            continue
        for desktop_file in base.glob("*.desktop"):
            try:
                text = desktop_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line in text.splitlines():
                if line.startswith("Exec="):
                    exec_cmd = line[len("Exec=") :].split()[0]
                    exec_cmd = exec_cmd.strip('"')
                    binary_name = Path(exec_cmd).name.lower()
                    resolved = shutil.which(exec_cmd) or (
                        exec_cmd if Path(exec_cmd).is_absolute() else None
                    )
                    if resolved:
                        result.setdefault(binary_name, resolved)
                    break
    return result


def _flatpak_app_ids() -> set[str]:
    if not shutil.which("flatpak"):
        return set()
    try:
        proc = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    except (subprocess.SubprocessError, OSError):
        return set()
