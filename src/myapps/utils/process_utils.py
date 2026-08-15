"""Safe subprocess launching helpers.

Project paths and editor paths are effectively user-controlled data, so we
never use shell=True and always pass argv as a list.
"""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def launch_detached(argv: list[str]) -> bool:
    """Launch a process detached from the app (it should keep running if the
    app quits). Returns True if the process was started successfully.
    """
    if not argv:
        logger.error("Empty argv, nothing to launch")
        return False
    try:
        subprocess.Popen(  # noqa: S603 - argv is a list, never shell=True
            argv,
            close_fds=True,
            start_new_session=True,
        )
        return True
    except (OSError, subprocess.SubprocessError):
        logger.exception("Failed to launch process: %s", argv)
        return False


def run_capture(argv: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess | None:
    """Run a short-lived process and capture its output. Returns None on failure."""
    try:
        return subprocess.run(  # noqa: S603
            argv, capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception("Failed to run process: %s", argv)
        return None
