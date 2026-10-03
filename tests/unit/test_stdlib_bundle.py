"""The packaged app bundles the full standard library for plugins - see
packaging/pyinstaller/stdlib_modules.py. These cover the module list and the
app's `--check-imports` mode from source; the frozen side is checked in CI
by packaging/pyinstaller/check_stdlib_bundle.py after each PyInstaller build.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packaging" / "pyinstaller"))

from stdlib_modules import EXCLUDED, stdlib_hiddenimports  # noqa: E402


def test_lists_the_modules_plugins_need():
    modules = set(stdlib_hiddenimports())
    for name in (
        "html",
        "html.parser",
        "concurrent.futures",
        "json",
        "sqlite3",
        "xml.etree.ElementTree",
        "email.mime.text",
        "urllib.request",
        "csv",
        "zipfile",
        "difflib",
        "asyncio",
        "zoneinfo",
    ):
        assert name in modules, name


def test_leaves_out_excluded_packages_tests_and_package_mains():
    for name in stdlib_hiddenimports():
        parts = name.split(".")
        assert parts[0] not in EXCLUDED, name
        assert not {"test", "tests", "idle_test", "__main__"} & set(parts[1:]), name


def test_list_is_sorted_and_unique():
    modules = stdlib_hiddenimports()
    assert modules == sorted(set(modules))


def test_check_imports_mode_reports_failures_without_starting_the_gui(tmp_path):
    names = tmp_path / "names.txt"
    names.write_text("json\nhtml\ndefinitely_not_a_module_xyz\n", encoding="utf-8")
    report = tmp_path / "report.json"

    subprocess.run(
        [sys.executable, "-m", "myapps", "--check-imports", str(names), str(report)],
        check=True,
        timeout=60,
        cwd=REPO_ROOT,
    )

    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["checked"] == 3
    assert list(result["failed"]) == ["definitely_not_a_module_xyz"]
