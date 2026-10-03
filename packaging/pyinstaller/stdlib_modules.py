"""The standard-library modules the frozen app bundles on top of what
PyInstaller's import analysis finds on its own.

Why: plugins are loaded at runtime from an external folder, so PyInstaller
never sees their imports - a frozen build otherwise contains only the stdlib
modules MyAppsLibrary's own code imports, and a plugin importing any other
one (`html`, `concurrent.futures`, ...) fails with ModuleNotFoundError in the
installed app while working fine from source. Bundling the whole stdlib
(minus EXCLUDED below) lets plugins rely on all of it.

Used by myapps.spec (as `hiddenimports`) and by check_stdlib_bundle.py's CI
check. Computed for the interpreter running the build, so each OS's build
gets that OS's modules (winreg/msvcrt on Windows only, fcntl/termios on
POSIX only, ...) - `find_spec` returning None simply skips the others.
Submodules are listed by walking package directories, never by importing
them, so this is cheap and has no side effects.
"""

from __future__ import annotations

import importlib.util
import os
import pkgutil
import sys

# Top-level stdlib names deliberately left out, and why:
EXCLUDED = {
    # Tk GUI toolkit and the apps built on it - this is a Qt app; Tk would
    # also drag in a whole Tcl/Tk runtime (several MB).
    "tkinter",
    "_tkinter",
    "turtle",
    "turtledemo",
    "idlelib",
    # CPython's own test suite and test-only helper modules.
    "test",
    "_testbuffer",
    "_testcapi",
    "_testclinic",
    "_testclinic_limited",
    "_testexternalinspection",
    "_testimportmultiple",
    "_testinternalcapi",
    "_testlimitedcapi",
    "_testmultiphase",
    "_testsinglephase",
    "_ctypes_test",
    "xxlimited",
    "xxlimited_35",
    "xxsubtype",
    "_xxtestfuzz",
    # Installing/creating Python environments is meaningless inside a frozen
    # app (no real interpreter on disk to point a venv at), and ensurepip
    # carries bundled pip wheels.
    "ensurepip",
    "venv",
    # Easter eggs / demo modules.
    "this",
    "antigravity",
    "__hello__",
    "__phello__",
    # The interactive help() topic database - large, and only useful to an
    # interactive interpreter prompt.
    "pydoc_data",
}

# Submodule path segments always skipped, at any depth: test code (e.g.
# `ctypes.test`, `idlelib.idle_test`), and a package's `__main__` - only
# ever meant for `python -m <package>`, which a frozen app never runs.
_SKIPPED_SEGMENTS = {"test", "tests", "idle_test", "__main__"}


def _is_excluded(dotted_name: str) -> bool:
    parts = dotted_name.split(".")
    return parts[0] in EXCLUDED or any(part in _SKIPPED_SEGMENTS for part in parts[1:])


def _walk_submodules(package: str, paths) -> list[str]:
    found: list[str] = []
    for info in pkgutil.iter_modules(paths):
        name = f"{package}.{info.name}"
        if _is_excluded(name):
            continue
        found.append(name)
        if info.ispkg:
            found.extend(_walk_submodules(name, [os.path.join(p, info.name) for p in paths]))
    return found


def stdlib_hiddenimports() -> list[str]:
    """Every importable stdlib module and submodule on this platform,
    except EXCLUDED and test packages - sorted, for a deterministic build."""
    names: set[str] = set()
    for top in sys.stdlib_module_names:
        if _is_excluded(top):
            continue
        try:
            spec = importlib.util.find_spec(top)
        except (ImportError, ValueError):
            spec = None
        if spec is None:
            continue  # not available on this OS/build of Python
        names.add(top)
        if spec.submodule_search_locations:
            names.update(_walk_submodules(top, list(spec.submodule_search_locations)))
    return sorted(names)


if __name__ == "__main__":
    modules = stdlib_hiddenimports()
    print("\n".join(modules))
    print(f"{len(modules)} modules", file=sys.stderr)
