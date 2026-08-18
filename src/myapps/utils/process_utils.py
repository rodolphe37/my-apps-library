"""Safe subprocess launching helpers.

Project paths and editor paths are effectively user-controlled data, so we
never use shell=True and always pass argv as a list.
"""

from __future__ import annotations

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def external_process_env() -> dict[str, str]:
    """The base environment for launching a process that ISN'T this app's
    own bundled Python interpreter (an editor, a terminal, a project's own
    toolchain via a plugin, ...).

    A PyInstaller-frozen build's bootloader points `DYLD_LIBRARY_PATH`
    (macOS) / `LD_LIBRARY_PATH` (Linux) at the bundle's own private lib
    directory, so the frozen interpreter finds its bundled shared libraries
    first - correct for re-invoking the bundled app itself, but poisonous
    for an unrelated external binary, which can end up loading the wrong
    libc/libssl/etc from inside the bundle instead of the system's, and
    fail or misbehave in ways that are easy to mistake for "the command
    doesn't exist". The bootloader saves whatever these variables were
    originally under a "_ORIG" suffix before overwriting them; restoring
    that (or dropping the variable entirely if there was nothing to
    restore, i.e. running unfrozen from source) gives external tools a
    clean environment, as if the packaged app never touched it."""
    env = dict(os.environ)
    for var in ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH"):
        original = env.pop(f"{var}_ORIG", None)
        if original:
            env[var] = original
        else:
            env.pop(var, None)
    return env


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
            env=external_process_env(),
        )
        return True
    except (OSError, subprocess.SubprocessError):
        logger.exception("Failed to launch process: %s", argv)
        return False


def run_capture(argv: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess | None:
    """Run a short-lived process and capture its output. Returns None on failure."""
    try:
        return subprocess.run(  # noqa: S603
            argv, capture_output=True, text=True, timeout=timeout, env=external_process_env()
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception("Failed to run process: %s", argv)
        return None
