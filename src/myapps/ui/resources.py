"""Resolves paths to bundled UI assets (icons, etc.), working both when
running from source and when frozen by PyInstaller (see
packaging/pyinstaller/myapps.spec, which bundles this `resources/` folder
the same way it already bundles `theme/styles`).
"""

from __future__ import annotations

import sys
from pathlib import Path

_RESOURCES_DIR = Path(__file__).parent / "resources"


def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller onedir/onefile: bundled data sits next to the executable
        # under the same relative path it was added at (see myapps.spec).
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "myapps" / "ui" / "resources" / Path(*parts)
    return _RESOURCES_DIR / Path(*parts)


def app_icon_path() -> Path:
    return resource_path("icons", "app.png")
