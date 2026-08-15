"""Regression coverage for the macOS editor detector's launch-strategy
priority: CLI shim on PATH > bundled CLI inside the .app > `open -a`
fallback. The `open -a --args` fallback is unreliable when the target app
is already running (macOS silently drops the args), so detection should
prefer a real CLI binary whenever one can be found.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from myapps.editors.detectors import macos


def _make_fake_app_bundle(base, app_name: str, *, with_bundled_cli: str | None = None):
    app_path = base / f"{app_name}.app"
    app_path.mkdir(parents=True)
    if with_bundled_cli:
        bin_dir = app_path / "Contents" / "Resources" / "app" / "bin"
        bin_dir.mkdir(parents=True)
        cli_path = bin_dir / with_bundled_cli
        cli_path.write_text("#!/bin/sh\necho fake cli\n", encoding="utf-8")
        cli_path.chmod(cli_path.stat().st_mode | stat.S_IEXEC)
    return app_path


def test_prefers_bundled_cli_over_open_dash_a(tmp_path, monkeypatch):
    monkeypatch.setattr(macos, "APPLICATIONS_DIRS", [tmp_path])
    monkeypatch.setattr("shutil.which", lambda name: None)  # nothing on PATH
    app_path = _make_fake_app_bundle(tmp_path, "Visual Studio Code", with_bundled_cli="code")

    results = macos.detect()
    vscode = next(r for r in results if r.id == "vscode")

    assert vscode.launch_strategy == "cli"
    # Compare as Path, not a hardcoded "/"-separated string - str(Path) uses
    # "\" on Windows, and this test (like the module under test) has no
    # platform guard so it runs on every CI OS.
    expected_cli = app_path / "Contents" / "Resources" / "app" / "bin" / "code"
    assert Path(vscode.executable_path) == expected_cli
    assert vscode.launch_template[0] == vscode.executable_path


def test_falls_back_to_open_dash_a_when_no_cli_available(tmp_path, monkeypatch):
    monkeypatch.setattr(macos, "APPLICATIONS_DIRS", [tmp_path])
    monkeypatch.setattr("shutil.which", lambda name: None)
    _make_fake_app_bundle(tmp_path, "Visual Studio Code")  # no bundled CLI

    results = macos.detect()
    vscode = next(r for r in results if r.id == "vscode")

    assert vscode.launch_strategy == "mac_open"
    assert vscode.launch_template[0] == "open"


def test_path_cli_shim_still_takes_priority_over_bundled_cli(tmp_path, monkeypatch):
    monkeypatch.setattr(macos, "APPLICATIONS_DIRS", [tmp_path])
    monkeypatch.setattr(
        "shutil.which", lambda name: "/usr/local/bin/code" if name == "code" else None
    )
    _make_fake_app_bundle(tmp_path, "Visual Studio Code", with_bundled_cli="code")

    results = macos.detect()
    vscode = next(r for r in results if r.id == "vscode")

    assert vscode.executable_path == "/usr/local/bin/code"


def test_bundled_cli_must_be_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(macos, "APPLICATIONS_DIRS", [tmp_path])
    monkeypatch.setattr("shutil.which", lambda name: None)
    app_path = _make_fake_app_bundle(tmp_path, "Visual Studio Code")
    bin_dir = app_path / "Contents" / "Resources" / "app" / "bin"
    bin_dir.mkdir(parents=True)
    non_exec = bin_dir / "code"
    non_exec.write_text("not executable", encoding="utf-8")

    # Simulate "not executable" via a mocked os.access rather than a real
    # chmod: Windows has no POSIX exec bit, so os.access(path, os.X_OK)
    # returns True there regardless of chmod, which would make this
    # assertion flaky depending on the CI OS.
    real_access = os.access

    def fake_access(path, mode, *args, **kwargs):
        if mode == os.X_OK and Path(path) == non_exec:
            return False
        return real_access(path, mode, *args, **kwargs)

    monkeypatch.setattr("os.access", fake_access)

    results = macos.detect()
    vscode = next(r for r in results if r.id == "vscode")

    assert vscode.launch_strategy == "mac_open"  # non-executable file is skipped
