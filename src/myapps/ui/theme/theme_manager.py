"""Applies light/dark theme: system detection (darkdetect + Qt's own signal)
plus a manual override, persisted in settings.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from myapps.ui.theme.palettes import dark_palette, light_palette

logger = logging.getLogger(__name__)

_STYLES_DIR = Path(__file__).parent / "styles"

try:
    import darkdetect
except ImportError:  # pragma: no cover - darkdetect is a declared dependency
    darkdetect = None


class ThemeManager(QObject):
    theme_changed = Signal(str)  # resolved theme: "light" | "dark"

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self._mode = "system"  # "system" | "light" | "dark"
        self._resolved = "light"

        style_hints = app.styleHints()
        if hasattr(style_hints, "colorSchemeChanged"):
            style_hints.colorSchemeChanged.connect(self._on_system_scheme_changed)

    def set_mode(self, mode: str) -> None:
        if mode not in ("system", "light", "dark"):
            logger.warning("Unknown theme mode %r, defaulting to system", mode)
            mode = "system"
        self._mode = mode
        self.apply()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def resolved_theme(self) -> str:
        return self._resolved

    def apply(self) -> None:
        theme = self._mode if self._mode != "system" else self._detect_system_theme()
        self._resolved = theme
        palette = dark_palette() if theme == "dark" else light_palette()
        self._app.setPalette(palette)
        self._app.setStyleSheet(self._load_qss(theme))
        self.theme_changed.emit(theme)

    def _on_system_scheme_changed(self, _scheme) -> None:
        if self._mode == "system":
            self.apply()

    @staticmethod
    def _detect_system_theme() -> str:
        if darkdetect is not None:
            try:
                detected = darkdetect.theme()
                if detected:
                    return detected.lower()
            except Exception:
                logger.exception("darkdetect failed, defaulting to light")
        return "light"

    @staticmethod
    def _load_qss(theme: str) -> str:
        qss_path = _STYLES_DIR / f"{theme}.qss"
        try:
            return qss_path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("Could not load stylesheet %s", qss_path)
            return ""
