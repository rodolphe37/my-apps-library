"""QPalette builders for light and dark themes. Take a token dict (see
ui/theme/tokens.py) — the built-in brand palette by default, or a plugin-
contributed ThemePalette's light/dark dict when the user picks one in
Preferences → Theme."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

from myapps.ui.theme.tokens import default_dark_tokens, default_light_tokens


def light_palette(tokens: dict[str, str] | None = None) -> QPalette:
    t = tokens or default_light_tokens()
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(t["bg"]))
    p.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Base, QColor(t["surface"]))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(t["surface_alt"]))
    p.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Button, QColor(t["surface_alt"]))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Highlight, QColor(t["accent_blend"]))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["surface"]))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["subtext"]))
    return p


def dark_palette(tokens: dict[str, str] | None = None) -> QPalette:
    t = tokens or default_dark_tokens()
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(t["bg"]))
    p.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Base, QColor(t["surface"]))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(t["surface_alt"]))
    p.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Button, QColor(t["surface_alt"]))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Highlight, QColor(t["accent_blend"]))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["surface_alt"]))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["subtext"]))
    return p
