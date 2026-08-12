"""Loads built-in locale files and builds a merged lookup for one locale.

No Qt imports — plain data, testable with plain pytest (mirrors core/'s
Qt-free layering).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

BUILTIN_LOCALES_DIR = Path(__file__).parent / "locales"
FALLBACK_LOCALE = "en"

logger = logging.getLogger(__name__)


def discover_builtin_locales() -> list[str]:
    """Sorted locale codes from every <code>.json under locales/."""
    if not BUILTIN_LOCALES_DIR.exists():
        return []
    return sorted(p.stem for p in BUILTIN_LOCALES_DIR.glob("*.json"))


def load_builtin_locale(locale: str) -> dict[str, str]:
    """Returns {} for a missing or malformed file — never raises."""
    path = BUILTIN_LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.exception("Failed to load built-in locale file %s", path)
        return {}
    if not isinstance(data, dict):
        logger.error("Locale file %s does not contain a JSON object", path)
        return {}
    return {str(k): str(v) for k, v in data.items()}


class TranslationCatalog:
    """Immutable merged key->value view for ONE resolved locale: built-in
    JSON (base) + plugin-contributed overrides (patched on top) + an English
    fallback layer underneath for keys missing from either."""

    def __init__(self, locale: str, entries: dict[str, str], fallback: dict[str, str]) -> None:
        self.locale = locale
        self._entries = entries
        self._fallback = fallback

    @classmethod
    def build(
        cls, locale: str, plugin_overrides: dict[str, str] | None = None
    ) -> TranslationCatalog:
        base = load_builtin_locale(locale)
        if plugin_overrides:
            base = {**base, **plugin_overrides}
        fallback = {} if locale == FALLBACK_LOCALE else load_builtin_locale(FALLBACK_LOCALE)
        return cls(locale, base, fallback)

    def get(self, key: str) -> str | None:
        if key in self._entries:
            return self._entries[key]
        if key in self._fallback:
            return self._fallback[key]
        return None
