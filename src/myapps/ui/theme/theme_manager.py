"""Applies light/dark theme: system detection (darkdetect + Qt's own signal)
plus a manual override, persisted in settings. Also resolves which color
*palette* is active - the built-in brand palette, or one contributed by an
enabled plugin (see plugins/api.py's ThemePalette) - and drives both the
native QPalette (ui/theme/palettes.py) and the `.qss` stylesheets
(templated with `string.Template`, see ui/theme/tokens.py) from the same
token dict, so a palette is only ever defined once.
"""

from __future__ import annotations

import logging
from pathlib import Path
from string import Template

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from myapps.plugins.api import ThemePalette
from myapps.ui.theme.palettes import dark_palette, light_palette
from myapps.ui.theme.tokens import default_dark_tokens, default_light_tokens

logger = logging.getLogger(__name__)

_STYLES_DIR = Path(__file__).parent / "styles"
DEFAULT_PALETTE_ID = "default"

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
        self._palette_id = DEFAULT_PALETTE_ID
        self._available_palettes: dict[str, ThemePalette] = {}

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

    # -- palette (color scheme) selection --------------------------------

    def set_available_palettes(self, palettes: list[ThemePalette]) -> None:
        """Call once after PluginManager has loaded every enabled plugin
        (and again if plugins are enabled/disabled at runtime) - see
        app.py and ui/dialogs/plugin_manager_dialog.py."""
        self._available_palettes = {p.id: p for p in palettes}

    def available_palette_choices(self) -> list[tuple[str, str]]:
        """(id, label) pairs for Preferences → Theme, built-in default
        first."""
        choices = [(DEFAULT_PALETTE_ID, "Default")]
        choices.extend((p.id, p.label) for p in self._available_palettes.values())
        return choices

    def set_palette(self, palette_id: str) -> None:
        """Falls back to the built-in default if `palette_id` doesn't match
        any currently-available plugin palette (e.g. its plugin was
        disabled/uninstalled since it was picked) - never raises, never
        leaves the app on a half-applied theme."""
        if palette_id != DEFAULT_PALETTE_ID and palette_id not in self._available_palettes:
            logger.info("Palette %r not available, falling back to default", palette_id)
            palette_id = DEFAULT_PALETTE_ID
        self._palette_id = palette_id
        self.apply()

    @property
    def palette_id(self) -> str:
        return self._palette_id

    def _current_tokens(self, theme: str) -> dict[str, str]:
        if self._palette_id == DEFAULT_PALETTE_ID:
            return default_light_tokens() if theme == "light" else default_dark_tokens()
        palette = self._available_palettes.get(self._palette_id)
        if palette is None:  # pragma: no cover - set_palette() already guards this
            return default_light_tokens() if theme == "light" else default_dark_tokens()
        return palette.light if theme == "light" else palette.dark

    # -- apply --------------------------------------------------------

    def apply(self) -> None:
        theme = self._mode if self._mode != "system" else self._detect_system_theme()
        self._resolved = theme
        tokens = self._current_tokens(theme)
        palette = dark_palette(tokens) if theme == "dark" else light_palette(tokens)
        self._app.setPalette(palette)
        self._app.setStyleSheet(self._load_qss(theme, tokens))
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
    def _load_qss(theme: str, tokens: dict[str, str]) -> str:
        qss_path = _STYLES_DIR / f"{theme}.qss"
        try:
            raw = qss_path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("Could not load stylesheet %s", qss_path)
            return ""
        try:
            return Template(raw).substitute(tokens)
        except KeyError:
            logger.exception("Stylesheet %s references an unknown token, using unfilled", qss_path)
            return Template(raw).safe_substitute(tokens)
