"""Windows editor detection: PATH, common install dirs, and the registry
App Paths key. JetBrains IDEs are detected via their Toolbox-generated shim
scripts (`*.cmd`), which is more reliable than guessing versioned install
paths under Program Files."""

from __future__ import annotations

import os
import shutil
import winreg  # only imported on Windows; this module is only loaded there
from pathlib import Path

from myapps.editors.base import EditorInfo
from myapps.editors.catalog import CATALOG

APP_PATHS_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"


def detect() -> list[EditorInfo]:
    found: list[EditorInfo] = []
    toolbox_shims = _jetbrains_toolbox_shims()
    program_dirs = _candidate_program_dirs()

    for entry in CATALOG:
        exe_path: str | None = None

        # 1. JetBrains Toolbox shim (covers the pycharm/idea/webstorm/etc family)
        for cli_name in entry.cli_names:
            shim = toolbox_shims.get(cli_name.lower())
            if shim:
                exe_path = shim
                break

        # 2. PATH
        if not exe_path:
            for cli_name in entry.cli_names:
                found_on_path = shutil.which(cli_name)
                if found_on_path:
                    exe_path = found_on_path
                    break

        # 3. Registry App Paths
        if not exe_path:
            for exe_name in entry.windows_exe_names:
                reg_path = _registry_app_path(exe_name)
                if reg_path:
                    exe_path = reg_path
                    break

        # 4. Common install directories (Program Files / LocalAppData)
        if not exe_path:
            for exe_name in entry.windows_exe_names:
                for base in program_dirs:
                    for hint in entry.windows_dir_hints:
                        candidate = base / hint
                        if candidate.exists():
                            match = next(candidate.rglob(exe_name), None)
                            if match:
                                exe_path = str(match)
                                break
                    if exe_path:
                        break
                if exe_path:
                    break

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


def _candidate_program_dirs() -> list[Path]:
    dirs = []
    for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        val = os.environ.get(var)
        if val:
            p = Path(val)
            if var == "LOCALAPPDATA":
                dirs.append(p / "Programs")
            else:
                dirs.append(p)
    return dirs


def _registry_app_path(exe_name: str) -> str | None:
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, f"{APP_PATHS_KEY}\\{exe_name}") as key:
                value, _ = winreg.QueryValueEx(key, None)
                if value and Path(value).exists():
                    return value
        except OSError:
            continue
    return None


def _jetbrains_toolbox_shims() -> dict[str, str]:
    """Map lowercase shim base name -> full path, e.g. {'pycharm': 'C:\\...\\pycharm.cmd'}."""
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        return {}
    scripts_dir = Path(local_appdata) / "JetBrains" / "Toolbox" / "scripts"
    if not scripts_dir.exists():
        return {}
    return {p.stem.lower(): str(p) for p in scripts_dir.glob("*.cmd")}
