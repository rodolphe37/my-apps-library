"""Translator: active-locale string lookup with placeholder interpolation.

No Qt imports. Module-level singleton `translator` + free function `tr()`,
same pattern as `core/events.py`'s `event_bus`.
"""

from __future__ import annotations

import logging

from myapps.i18n.catalog import FALLBACK_LOCALE, TranslationCatalog, discover_builtin_locales

logger = logging.getLogger(__name__)

LANGUAGE_NAME_KEY = "meta.language_name"


class Translator:
    def __init__(self) -> None:
        self._locale = FALLBACK_LOCALE
        self._plugin_translations: dict[str, dict[str, str]] = {}
        self._catalog = TranslationCatalog.build(self._locale)

    def set_locale(self, locale: str) -> None:
        self._locale = locale
        self._catalog = TranslationCatalog.build(
            locale, self._plugin_translations.get(locale)
        )

    @property
    def locale(self) -> str:
        return self._locale

    def set_plugin_translations(self, plugin_translations: dict[str, dict[str, str]]) -> None:
        """`plugin_translations` is PluginManager.collect_translations()'s
        already-merged-across-plugins result: {locale: {key: value}}."""
        self._plugin_translations = plugin_translations
        # Rebuild the active catalog in case the currently-selected locale's
        # plugin overrides just changed (a plugin was enabled/disabled).
        self.set_locale(self._locale)

    def available_locales(self) -> set[str]:
        """Built-in locales union any locale a currently-loaded plugin
        contributes — this is what powers the Settings dropdown."""
        return set(discover_builtin_locales()) | set(self._plugin_translations.keys())

    def display_name(self, locale: str) -> str:
        """Builds a throwaway catalog for `locale` (does NOT mutate active
        state) and reads the reserved key 'meta.language_name' — e.g.
        fr.json's own entry for that key is 'Français'. Falls back to the
        locale code if absent."""
        catalog = TranslationCatalog.build(locale, self._plugin_translations.get(locale))
        return catalog.get(LANGUAGE_NAME_KEY) or locale

    def tr(self, key: str, **kwargs) -> str:
        """Active-catalog lookup -> the key itself if missing (visibly-wrong
        beats silently-blank), then str.format(**kwargs) tolerant of a
        missing/mismatched placeholder (never raises out of a widget's
        __init__)."""
        template = self._catalog.get(key)
        if template is None:
            logger.warning("Missing translation key: %r", key)
            template = key
        if not kwargs:
            return template
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            logger.warning("Bad placeholder(s) in translation %r with kwargs %r", key, kwargs)
            return template


translator = Translator()


def tr(key: str, **kwargs) -> str:
    return translator.tr(key, **kwargs)
