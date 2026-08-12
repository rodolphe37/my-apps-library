"""QPalette builders for light and dark themes, using the brand colors in
brand.py (sampled from the app logo)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

from myapps.ui.theme import brand


def light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(brand.LIGHT_BG))
    p.setColor(QPalette.ColorRole.WindowText, QColor(brand.LIGHT_TEXT))
    p.setColor(QPalette.ColorRole.Base, QColor(brand.LIGHT_SURFACE))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(brand.LIGHT_SURFACE_ALT))
    p.setColor(QPalette.ColorRole.Text, QColor(brand.LIGHT_TEXT))
    p.setColor(QPalette.ColorRole.Button, QColor(brand.LIGHT_SURFACE_ALT))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(brand.LIGHT_TEXT))
    p.setColor(QPalette.ColorRole.Highlight, QColor(brand.ACCENT_BLEND))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(brand.LIGHT_SURFACE))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(brand.LIGHT_TEXT))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(brand.LIGHT_SUBTEXT))
    return p


def dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(brand.DARK_BG))
    p.setColor(QPalette.ColorRole.WindowText, QColor(brand.DARK_TEXT))
    p.setColor(QPalette.ColorRole.Base, QColor(brand.DARK_SURFACE))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(brand.DARK_SURFACE_ALT))
    p.setColor(QPalette.ColorRole.Text, QColor(brand.DARK_TEXT))
    p.setColor(QPalette.ColorRole.Button, QColor(brand.DARK_SURFACE_ALT))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(brand.DARK_TEXT))
    p.setColor(QPalette.ColorRole.Highlight, QColor(brand.ACCENT_BLEND))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(brand.DARK_SURFACE_ALT))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(brand.DARK_TEXT))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(brand.DARK_SUBTEXT))
    return p
