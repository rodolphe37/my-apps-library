"""Example plugin: adds German (Deutsch) as a full, selectable language.
Exercises the translation-plugin extension point end-to-end — the same
validation role the two Phase 2 example plugins played for the core plugin
API. Covers every key present in the app's built-in en.json/fr.json.

Translations live in `de.json`, right next to this file — the same JSON
format the app itself uses for its built-in locales (src/myapps/i18n/locales/),
so a translation-plugin author never has to write a Python dict literal by
hand, just edit a plain JSON file.

To try it: copy this folder into your MyAppsLibrary plugins directory (see
paths.plugins_dir()), then enable it from Plugins > Manage Plugins — you'll
see "Deutsch" become selectable in Preferences > Language.
"""

from __future__ import annotations

import json
from pathlib import Path

from myapps.plugins.api import PluginBase, PluginContext

TRANSLATIONS_FILE = Path(__file__).parent / "de.json"


class GermanTranslationPlugin(PluginBase):
    def on_load(self, ctx: PluginContext) -> None:
        self._translations = self._load_translations(ctx)
        ctx.logger.info("German translation plugin loaded (%d keys)", len(self._translations))

    def contribute_translations(self) -> dict[str, dict[str, str]]:
        return {"de": self._translations}

    @staticmethod
    def _load_translations(ctx: PluginContext) -> dict[str, str]:
        try:
            with TRANSLATIONS_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return {str(k): str(v) for k, v in data.items()}
        except (OSError, json.JSONDecodeError):
            ctx.logger.exception("Failed to load %s", TRANSLATIONS_FILE)
            return {}
