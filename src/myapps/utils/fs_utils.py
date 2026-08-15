"""Cross-platform "reveal in file manager" and path validation helpers."""

from __future__ import annotations

import logging
import os
import platform
import shutil
from pathlib import Path

from myapps.utils.process_utils import launch_detached, run_capture

logger = logging.getLogger(__name__)


def directory_size(path: str) -> int:
    """Total size in bytes of every regular file under `path`, recursively.
    Best-effort: unreadable entries and broken symlinks are skipped rather
    than raising, and symlinked directories are never followed (avoids
    cycles) - same tolerance-over-precision tradeoff as the rest of this
    module. Returns 0 for a path that doesn't exist or isn't a directory.

    Can be slow for very large trees (deep node_modules/.git, etc.) since
    it's a full recursive walk with no caching of its own - callers that
    need this repeatedly (e.g. sort-by-size) should cache the result
    themselves; see ui/models/project_list_model.py.
    """
    total = 0
    for root, _dirs, files in os.walk(path, onerror=lambda _err: None):
        for filename in files:
            try:
                total += os.path.getsize(os.path.join(root, filename))
            except OSError:
                continue  # permission denied, broken symlink, race with deletion, etc.
    return total

_SELECT_FLAG_BY_FILE_MANAGER = {
    "nautilus": "--select",
    "dolphin": "--select",
    "nemo": None,  # nemo has no reliable select flag; falls back to opening the folder
    "pcmanfm": None,
    "thunar": None,
}


def reveal_in_file_manager(path: str) -> bool:
    """Open the OS file manager with `path` selected/highlighted, or at least
    open its parent folder if selection isn't supported.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        logger.error("Cannot reveal nonexistent path: %s", resolved)
        return False

    system = platform.system()
    if system == "Darwin":
        return launch_detached(["open", "-R", str(resolved)])
    elif system == "Windows":
        # `explorer` frequently returns a nonzero exit code even on success,
        # so we don't treat that as failure - only a launch exception counts.
        return launch_detached(["explorer", f"/select,{resolved}"])
    elif system == "Linux":
        return _reveal_linux(resolved)
    else:
        logger.warning("Unsupported platform for reveal-in-file-manager: %s", system)
        return False


def _reveal_linux(resolved: Path) -> bool:
    file_manager = _default_linux_file_manager()
    parent = resolved.parent

    if file_manager:
        select_flag = _SELECT_FLAG_BY_FILE_MANAGER.get(file_manager)
        if select_flag and shutil.which(file_manager):
            return launch_detached([file_manager, select_flag, str(resolved)])
        if shutil.which(file_manager):
            return launch_detached([file_manager, str(parent)])

    # Fallback: just open the parent folder with the system default handler.
    if shutil.which("xdg-open"):
        return launch_detached(["xdg-open", str(parent)])

    logger.error("No known way to reveal files on this Linux desktop environment")
    return False


def _default_linux_file_manager() -> str | None:
    if not shutil.which("xdg-mime"):
        return None
    result = run_capture(["xdg-mime", "query", "default", "inode/directory"])
    if not result or result.returncode != 0:
        return None
    desktop_file = result.stdout.strip()  # e.g. "org.gnome.Nautilus.desktop"
    lowered = desktop_file.lower()
    for name in _SELECT_FLAG_BY_FILE_MANAGER:
        if name in lowered:
            return name
    return None
