"""Cross-platform standard directories for app data, config, cache, and logs."""

from __future__ import annotations

from pathlib import Path

from platformdirs import PlatformDirs

from myapps.constants import APP_ID, ORG_NAME

_dirs = PlatformDirs(appname=APP_ID, appauthor=ORG_NAME, roaming=True)


def data_dir() -> Path:
    p = Path(_dirs.user_data_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def cache_dir() -> Path:
    p = Path(_dirs.user_cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def log_dir() -> Path:
    p = data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def plugins_dir() -> Path:
    p = data_dir() / "plugins"
    p.mkdir(parents=True, exist_ok=True)
    return p


def library_file() -> Path:
    return data_dir() / "library.json"


def settings_file() -> Path:
    return data_dir() / "settings.json"


def editors_file() -> Path:
    return data_dir() / "editors.json"
