"""Get/set for app-wide settings, backed by settings.json."""

from __future__ import annotations

from pathlib import Path

from myapps.core.events import event_bus
from myapps.core.models import AppSettings
from myapps.core.store import load_json, save_json
from myapps.paths import settings_file


class SettingsManager:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or settings_file()
        self._settings = AppSettings.from_dict(load_json(self._path, default={}))

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def set(self, **fields) -> None:
        changed = []
        for key, value in fields.items():
            if hasattr(self._settings, key) and getattr(self._settings, key) != value:
                setattr(self._settings, key, value)
                changed.append(key)
        if changed:
            self._save()
            for field_name in changed:
                event_bus.settings_changed.emit(field_name)

    def _save(self) -> None:
        save_json(self._path, self._settings.to_dict())
