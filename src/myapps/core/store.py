"""Atomic JSON read/write helpers shared by all persistence modules.

Isolating this here means a future switch to SQLite (if it's ever warranted)
only touches this module, not ProjectManager/SettingsManager/EditorRegistry.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from myapps.constants import SCHEMA_VERSION

logger = logging.getLogger(__name__)


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    """Load a JSON file, returning `default` if it doesn't exist or is corrupt."""
    if not path.exists():
        return dict(default)
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("root JSON value must be an object")
        return data
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        logger.error("Failed to load %s (%s); backing up and starting fresh", path, exc)
        _quarantine_corrupt_file(path)
        return dict(default)


def save_json(path: Path, data: dict[str, Any]) -> None:
    """Atomically write `data` as JSON to `path` (temp file + os.replace).

    This avoids leaving a half-written, corrupt file if the process is killed
    mid-write.
    """
    data = {"schema_version": SCHEMA_VERSION, **data}
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _quarantine_corrupt_file(path: Path) -> None:
    if not path.exists():
        return
    backup = path.with_suffix(path.suffix + ".corrupt")
    try:
        os.replace(path, backup)
    except OSError:
        logger.exception("Could not quarantine corrupt file %s", path)
