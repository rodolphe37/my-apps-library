"""Reusable painted shapes for the app's blue-to-purple brand gradient
(see brand.py's ACCENT_BLUE/ACCENT_PURPLE) - kept separate from any single
widget so the same silhouette renders identically everywhere it's used:
`ui/delegates/project_item_delegate.py`'s list/grid rows, and
`ui/dialogs/plugin_manager_dialog.py`'s generated fallback icon for a
plugin with no logo of its own.

Two shapes:

- `paint_folder_icon()` - an actual folder silhouette (a narrower "tab"
  merged with a wider body beneath it, not just a plain rounded square)
  reserved for real folders/projects.
- `paint_badge()` - a plain rounded-square badge, same gradient family,
  for anything that isn't a folder (e.g. a plugin's fallback icon) so the
  two never get visually confused for one another.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from myapps.ui.theme import brand


def brand_gradient(rect: QRect | QRectF) -> QLinearGradient:
    """Diagonal blue -> purple gradient matching the app logo."""
    gradient = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomRight()))
    gradient.setColorAt(0.0, QColor(brand.ACCENT_BLUE))
    gradient.setColorAt(1.0, QColor(brand.ACCENT_PURPLE))
    return gradient


def paint_folder_icon(painter: QPainter, rect: QRect, glyph: str | None = None) -> None:
    """A real folder silhouette: a narrower "tab" rect merged with a
    full-width "body" rect beneath it (QPainterPath.united(), so the seam
    between the two is invisible), both filled with one continuous
    gradient computed over the whole `rect` - not two separately-gradiented
    pieces, which would show a visible seam. Proportions are relative to
    `rect`, so this scales cleanly from an 18px list-view glyph up to a
    96px Get Info-style preview."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    tab_height = rect.height() * 0.24
    tab_width = rect.width() * 0.55
    corner = max(2.0, min(rect.width(), rect.height()) * 0.16)
    body_top = rect.top() + tab_height

    tab = QPainterPath()
    tab.addRoundedRect(
        QRectF(rect.left(), rect.top(), tab_width, tab_height + corner), corner, corner
    )
    body = QPainterPath()
    body.addRoundedRect(
        QRectF(rect.left(), body_top, rect.width(), rect.height() - tab_height), corner, corner
    )
    painter.fillPath(tab.united(body), brand_gradient(rect))

    # A soft lighter sheen across the top of the body, suggesting the fold
    # where the tab meets the main pocket - subtle, not a hard second color.
    sheen = QPainterPath()
    sheen.addRoundedRect(
        QRectF(rect.left(), body_top, rect.width(), (rect.height() - tab_height) * 0.45),
        corner,
        corner,
    )
    painter.fillPath(sheen, QColor(255, 255, 255, 40))

    if glyph:
        _draw_centered_glyph(
            painter,
            QRect(rect.left(), int(body_top), rect.width(), int(rect.height() - tab_height)),
            glyph,
        )
    painter.restore()


def paint_badge(painter: QPainter, rect: QRect, glyph: str | None = None) -> None:
    """A plain rounded-square badge in the same brand gradient - for
    anything that isn't a folder (e.g. a plugin with no logo of its own),
    so it never reads as a folder/project by mistake."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    radius = min(rect.width(), rect.height()) * 0.24
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), radius, radius)
    painter.fillPath(path, brand_gradient(rect))
    if glyph:
        _draw_centered_glyph(painter, rect, glyph)
    painter.restore()


def _draw_centered_glyph(painter: QPainter, rect: QRect, glyph: str) -> None:
    font = painter.font()
    font.setPointSizeF(rect.height() * 0.5)
    painter.setFont(font)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, glyph)


def folder_icon_pixmap(size: int, glyph: str | None = None) -> QPixmap:
    """`paint_folder_icon()` rendered onto a standalone, transparent-backed
    QPixmap - for the (non-delegate) places that need an actual QPixmap/
    QIcon rather than painting directly into an existing QPainter, e.g. a
    plain QLabel.setPixmap()."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    paint_folder_icon(painter, QRect(0, 0, size, size), glyph)
    painter.end()
    return pixmap


def badge_pixmap(size: int, glyph: str | None = None) -> QPixmap:
    """`paint_badge()`'s QPixmap equivalent - see `folder_icon_pixmap()`."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    paint_badge(painter, QRect(0, 0, size, size), glyph)
    painter.end()
    return pixmap


def apply_elevation(
    widget: QWidget, *, blur: float = 24.0, y_offset: float = 6.0, alpha: int = 60
) -> QGraphicsDropShadowEffect:
    """Installs a real drop shadow on a QWidget via QGraphicsDropShadowEffect.

    QSS has no `box-shadow` - Qt Style Sheets simply don't support it - so
    any actual elevation on a real widget (a dialog card, a toolbar, a
    button) has to go through this Python-side effect instead. It only
    works on genuine QWidgets, never inside a QAbstractItemDelegate.paint()
    call (list/grid rows are painted, not widgets) - see
    `project_item_delegate.py`'s own hand-painted soft-shadow for that case.

    One shared, low-key shadow color/alpha by default so elevation reads
    consistently across the app rather than each call site inventing its
    own; callers needing a stronger or colored glow (e.g. a primary
    gradient button) can override `blur`/`y_offset`/`alpha` or restyle the
    returned effect directly (e.g. `.setColor(...)`).
    """
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(0)
    effect.setYOffset(y_offset)
    effect.setColor(QColor(10, 14, 30, alpha))
    widget.setGraphicsEffect(effect)
    return effect


def paint_soft_shadow(
    painter: QPainter,
    rect: QRect | QRectF,
    radius: float,
    *,
    layers: int = 5,
    y_offset: float = 3.0,
) -> None:
    """Hand-paints a soft shadow behind `rect` for delegate-painted content
    (QGraphicsDropShadowEffect only applies to real QWidgets - see
    `apply_elevation()` - so a list/grid row painted inside
    QStyledItemDelegate.paint() has to fake elevation this way instead:
    several progressively larger, progressively fainter rounded rects,
    offset slightly downward, drawn *before* the row/tile's own
    background). Cheap enough for a handful of visible rows/tiles; not
    meant for large lists painted every frame."""
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    base_rect = QRectF(rect)
    for i in range(layers, 0, -1):
        spread = i * 1.6
        alpha = int(9 * (layers - i + 1) / layers) + 2
        layer_rect = base_rect.adjusted(-spread, -spread + y_offset, spread, spread + y_offset)
        path = QPainterPath()
        path.addRoundedRect(layer_rect, radius + spread, radius + spread)
        painter.fillPath(path, QColor(10, 14, 30, alpha))
    painter.restore()
