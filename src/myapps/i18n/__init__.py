"""Public i18n surface: `from myapps.i18n import tr` is the standard import
used across every UI file."""

from myapps.i18n.language_manager import LanguageManager
from myapps.i18n.translator import tr, translator

__all__ = ["tr", "translator", "LanguageManager"]
