"""Small hand-painted line icons for the main window's toolbar (view-mode
switch, sort button) - see main_window.py's _build_toolbar()/
_populate_view_toggle(). Painted with QPainter rather than font glyphs
(Unicode symbols like "☰"/"▦" render inconsistently across the system fonts
on Windows/macOS/Linux - a real risk given this app is meant to look
pixel-identical on all three, see ui/theme/brand.py's own cross-platform
framing) or SVG assets (none currently shipped anywhere in the app).

Each icon is built as a two-state QIcon - a muted "Off" pixmap and an
accent-colored "On" one - so a checkable QToolButton just works via Qt's own
QIcon.State.Off/On mechanism with no extra wiring on click/theme change.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

_CANVAS = 20  # design grid the coordinates below are laid out on


def _new_pixmap(size: int, color: QColor) -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color, max(1.4, size * 0.11))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.scale(size / _CANVAS, size / _CANVAS)
    return pixmap, painter


def _list_lines(painter: QPainter) -> None:
    for y in (5, 10, 15):
        painter.drawLine(3, y, 17, y)


def _sort_lines(painter: QPainter) -> None:
    painter.drawLine(3, 6, 17, 6)
    painter.drawLine(3, 10, 12, 10)
    painter.drawLine(3, 14, 8, 14)


def _rows_lines(painter: QPainter) -> None:
    """Fallback glyph for a plugin-contributed view mode this app can't
    otherwise identify a shape for (see main_window._populate_view_toggle) -
    3 lines like the plain list icon, plus a small leading tick on each so
    it doesn't read as an exact duplicate of the built-in List button."""
    for y in (5, 10, 15):
        painter.drawLine(3, y, 4.5, y)
        painter.drawLine(6.5, y, 17, y)


_BUILDERS = {
    # "grid" is deliberately absent - _paint() special-cases it (filled
    # squares via a brush, not stroked lines via a pen like the others) and
    # never looks it up here; it's still a recognized `kind` per
    # icon_kind_for_mode()'s _KNOWN_KINDS set below.
    "list": _list_lines,
    "sort": _sort_lines,
    "rows": _rows_lines,
}
_KNOWN_KINDS = {*_BUILDERS, "grid"}


def _paint(kind: str, size: int, color: QColor) -> QPixmap:
    if kind == "grid":
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(size / _CANVAS, size / _CANVAS)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        for x, y in ((3, 3), (11, 3), (3, 11), (11, 11)):
            painter.drawRoundedRect(QRectF(x, y, 6, 6), 1.5, 1.5)
        painter.end()
        return pixmap

    pixmap, painter = _new_pixmap(size, color)
    _BUILDERS[kind](painter)
    painter.end()
    return pixmap


def toolbar_icon(kind: str, size: int, off_color: QColor, on_color: QColor | None = None) -> QIcon:
    """A `kind` in {"list", "grid", "sort", "rows"}. `on_color` is only
    needed for a checkable button - omit it for the (non-checkable) sort
    button."""
    icon = QIcon()
    icon.addPixmap(_paint(kind, size, off_color), QIcon.Mode.Normal, QIcon.State.Off)
    if on_color is not None:
        icon.addPixmap(_paint(kind, size, on_color), QIcon.Mode.Normal, QIcon.State.On)
    return icon


def icon_kind_for_mode(mode_id: str) -> str:
    """Maps a view-mode id to one of this module's known icon kinds - the
    two built-ins get their own glyph, anything else (a plugin-contributed
    view mode, e.g. a Finder-style detailed list) falls back to "rows"
    rather than guessing at a shape this module has no way to know."""
    if mode_id in _KNOWN_KINDS and mode_id != "sort":
        return mode_id
    return "rows"


TOOLBAR_ICON_SIZE = QSize(17, 17)
