"""LanguageManager: system-locale detection + live language switching.

Structural mirror of ui/theme/theme_manager.py's ThemeManager: a `mode`
property ("system" or a locale code), `apply()`, and one Qt signal that the
UI connects to directly (not routed through the shared event_bus — same
reasoning theme switching doesn't route through it either: this is a
dedicated, UI-facing runtime signal, not a generic data-change notification).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QLocale, QObject, Signal

from myapps.i18n.catalog import FALLBACK_LOCALE
from myapps.i18n.translator import translator

logger = logging.getLogger(__name__)


class LanguageManager(QObject):
    language_changed = Signal(str)  # resolved locale, e.g. "en" | "fr"

    def __init__(self) -> None:
        super().__init__()
        self._mode = "system"
        self._resolved_locale = FALLBACK_LOCALE

    def set_mode(self, mode: str) -> None:
        self._mode = mode or "system"
        self.apply()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def resolved_locale(self) -> str:
        return self._resolved_locale

    def apply(self) -> None:
        locale = self._mode if self._mode != "system" else self._detect_system_locale()
        self._resolved_locale = locale
        translator.set_locale(locale)
        self.language_changed.emit(locale)

    def set_plugin_translations(self, plugin_translations: dict[str, dict[str, str]]) -> None:
        """Called at startup and again whenever the plugin set changes
        (enable/disable/install/uninstall) — updates the translator, then
        re-applies since a plugin enable/disable can add or remove the
        currently active locale's availability."""
        translator.set_plugin_translations(plugin_translations)
        self.apply()

    def _detect_system_locale(self) -> str:
        try:
            system_name = QLocale.system().name()  # e.g. "fr_FR", "en_US"
            language_subtag = system_name.split("_")[0].lower()
        except Exception:
            logger.exception("Failed to detect system locale, defaulting to %r", FALLBACK_LOCALE)
            return FALLBACK_LOCALE
        if language_subtag in translator.available_locales():
            return language_subtag
        return FALLBACK_LOCALE
