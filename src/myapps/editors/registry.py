"""Detects installed editors, merges with manually-added ones, caches to
editors.json, and launches a project folder in a chosen editor."""

from __future__ import annotations

import logging
import platform
import uuid
from pathlib import Path

from myapps.core.events import event_bus
from myapps.core.store import load_json, save_json
from myapps.editors.base import EditorInfo
from myapps.paths import editors_file
from myapps.utils.process_utils import launch_detached

logger = logging.getLogger(__name__)


class EditorRegistry:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or editors_file()
        self._editors: dict[str, EditorInfo] = {}
        self._load()

    # -- persistence ---------------------------------------------------

    def _load(self) -> None:
        data = load_json(self._path, default={"editors": []})
        self._editors = {
            e["id"]: EditorInfo.from_dict(e) for e in data.get("editors", [])
        }

    def _save(self) -> None:
        save_json(self._path, {"editors": [e.to_dict() for e in self._editors.values()]})

    # -- detection -------------------------------------------------------

    def refresh(self) -> list[EditorInfo]:
        """Re-run OS detection and merge results with existing manual entries.
        Detected entries are fully replaced (so uninstalled editors drop out);
        manual entries are preserved as-is.
        """
        detected = self._detect_for_current_os()
        manual = {eid: e for eid, e in self._editors.items() if e.kind == "manual"}
        self._editors = {e.id: e for e in detected}
        self._editors.update(manual)
        self._save()
        event_bus.editors_refreshed.emit()
        return self.list_editors()

    @staticmethod
    def _detect_for_current_os() -> list[EditorInfo]:
        system = platform.system()
        try:
            if system == "Darwin":
                from myapps.editors.detectors import macos

                return macos.detect()
            elif system == "Windows":
                from myapps.editors.detectors import windows

                return windows.detect()
            elif system == "Linux":
                from myapps.editors.detectors import linux

                return linux.detect()
        except Exception:
            logger.exception("Editor detection failed for %s", system)
        return []

    # -- CRUD --------------------------------------------------------------

    def list_editors(self) -> list[EditorInfo]:
        return sorted(self._editors.values(), key=lambda e: e.display_name.lower())

    def get_editor(self, editor_id: str) -> EditorInfo | None:
        return self._editors.get(editor_id)

    def add_manual_editor(self, display_name: str, executable_path: str) -> EditorInfo:
        editor = EditorInfo(
            id=f"manual:{uuid.uuid4().hex}",
            display_name=display_name,
            executable_path=executable_path,
            kind="manual",
            launch_strategy="cli",
            launch_template=[executable_path, "{path}"],
        )
        self._editors[editor.id] = editor
        self._save()
        event_bus.editors_refreshed.emit()
        return editor

    def remove_manual_editor(self, editor_id: str) -> None:
        editor = self._editors.get(editor_id)
        if editor and editor.kind == "manual":
            del self._editors[editor_id]
            self._save()
            event_bus.editors_refreshed.emit()

    # -- launch --------------------------------------------------------------

    def launch(self, editor_id: str, project_path: str) -> bool:
        editor = self._editors.get(editor_id)
        if editor is None:
            logger.error("Unknown editor id: %s", editor_id)
            return False
        argv = [arg.replace("{path}", project_path) for arg in editor.launch_template]
        return launch_detached(argv)
