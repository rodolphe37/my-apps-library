"""CI check: the frozen app can import every standard-library module a
source run of the same Python can - so plugins can rely on the full stdlib
(see stdlib_modules.py for why that isn't PyInstaller's default).

Run from the repo root after `pyinstaller packaging/pyinstaller/myapps.spec`:

    python packaging/pyinstaller/check_stdlib_bundle.py

Both sides go through the app's own `--check-imports` mode (myapps/
__main__.py): once with this interpreter from source, once with the built
executable. A module failing from source too (platform-specific submodules
like `multiprocessing.popen_spawn_win32` on macOS) is fine; one that only
fails frozen is a bundling bug, and fails the check. A few representative
modules must additionally import cleanly in the frozen app no matter what.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stdlib_modules import stdlib_hiddenimports  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST = REPO_ROOT / "dist"

# Must import in the frozen app on every OS - the modules plugins reach for
# most, including the two that were actually missing before (html,
# concurrent.futures).
REQUIRED = [
    "html",
    "html.parser",
    "concurrent.futures",
    "json",
    "sqlite3",
    "xml.etree.ElementTree",
    "email.mime.text",
    "urllib.request",
    "http.client",
    "csv",
    "zipfile",
    "tarfile",
    "difflib",
    "asyncio",
    "statistics",
    "zoneinfo",
    "tomllib",
    "uuid",
    "ssl",
]


def frozen_executable() -> Path:
    if sys.platform == "darwin":
        return DIST / "MyAppsLibrary.app" / "Contents" / "MacOS" / "MyAppsLibrary"
    if sys.platform == "win32":
        return DIST / "MyAppsLibrary" / "MyAppsLibrary.exe"
    return DIST / "MyAppsLibrary" / "MyAppsLibrary"


def run_check(argv: list[str], names_file: Path, report_file: Path) -> dict[str, str]:
    subprocess.run(  # noqa: S603 - fixed argv, no shell
        [*argv, "--check-imports", str(names_file), str(report_file)],
        check=True,
        timeout=300,
        cwd=REPO_ROOT,
    )
    return json.loads(report_file.read_text(encoding="utf-8"))["failed"]


def main() -> int:
    exe = frozen_executable()
    if not exe.exists():
        print(f"Frozen executable not found: {exe} - build it first.", file=sys.stderr)
        return 2

    modules = sorted(set(stdlib_hiddenimports()) | set(REQUIRED))
    with tempfile.TemporaryDirectory() as tmp:
        names_file = Path(tmp) / "modules.txt"
        names_file.write_text("\n".join(modules) + "\n", encoding="utf-8")
        from_source = run_check(
            [sys.executable, "-m", "myapps"], names_file, Path(tmp) / "source.json"
        )
        frozen = run_check([str(exe)], names_file, Path(tmp) / "frozen.json")

    only_frozen = {name: err for name, err in frozen.items() if name not in from_source}
    required_missing = {name: frozen[name] for name in REQUIRED if name in frozen}

    print(
        f"Checked {len(modules)} stdlib modules: {len(from_source)} unavailable from source "
        f"on this platform, {len(frozen)} unavailable frozen."
    )
    if only_frozen or required_missing:
        for name, err in sorted({**only_frozen, **required_missing}.items()):
            print(f"  MISSING in frozen app: {name} ({err})")
        return 1
    print("OK: the frozen app imports every stdlib module a source run can.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
