"""QPalette builders for light and dark themes."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette


def light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor("#f5f5f7"))
    p.setColor(QPalette.ColorRole.WindowText, QColor("#1d1d1f"))
    p.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#f0f0f2"))
    p.setColor(QPalette.ColorRole.Text, QColor("#1d1d1f"))
    p.setColor(QPalette.ColorRole.Button, QColor("#e8e8ea"))
    p.setColor(QPalette.ColorRole.ButtonText, QColor("#1d1d1f"))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#0a84ff"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor("#1d1d1f"))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8e8e93"))
    return p


def dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
    p.setColor(QPalette.ColorRole.WindowText, QColor("#f2f2f2"))
    p.setColor(QPalette.ColorRole.Base, QColor("#252526"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#2d2d2e"))
    p.setColor(QPalette.ColorRole.Text, QColor("#f2f2f2"))
    p.setColor(QPalette.ColorRole.Button, QColor("#333334"))
    p.setColor(QPalette.ColorRole.ButtonText, QColor("#f2f2f2"))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#0a84ff"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#333334"))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor("#f2f2f2"))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8e8e93"))
    return p
