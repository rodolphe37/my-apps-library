"""Reusable painted shapes for the app's blue-to-purple brand gradient
(see brand.py's ACCENT_BLUE/ACCENT_PURPLE) - kept separate from any single
widget so the same silhouette renders identically everywhere it's used:
`ui/delegates/project_item_delegate.py`'s list/grid rows,
`ui/widgets/category_sidebar.py`'s selected-row gradient, and
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
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget

from myapps.ui.theme import brand

# Key ThemeManager.apply() stashes the resolved token dict under on the
# QApplication instance (a dynamic property, not a new Qt API) - see its
# own docstring. Reading it back here is how a *painted* gradient (which
# can't reference `$accent_blue`/`$accent_purple` QSS tokens the way a
# stylesheet rule can) still honors a plugin-contributed ThemePalette
# instead of always falling back to the hardcoded default brand colors.
_ACTIVE_TOKENS_PROPERTY = "myapps_active_tokens"


def _active_accent_colors() -> tuple[str, str]:
    app = QApplication.instance()
    tokens = app.property(_ACTIVE_TOKENS_PROPERTY) if app else None
    if isinstance(tokens, dict):
        blue = tokens.get("accent_blue")
        purple = tokens.get("accent_purple")
        if isinstance(blue, str) and isinstance(purple, str):
            return blue, purple
    return brand.ACCENT_BLUE, brand.ACCENT_PURPLE


def active_token(key: str, fallback: str) -> QColor:
    """Any single token (e.g. "surface", "subtext") from the currently
    active palette - built-in or plugin-contributed - for delegate paint()
    code that needs an exact theme color. Deliberately NOT `option.palette`:
    once a global QSS is applied (this app always has one active), Qt's
    style-sheet cascade can recompute a widget's effective QPalette roles
    from the stylesheet rather than leaving them as the plain app palette
    (e.g. QListView's own `background-color: transparent` rule bleeding
    into `option.palette.base()`), so a delegate reading `option.palette`
    for a *fill* color can silently get the wrong shade. Reading the same
    token dict `brand_gradient()` uses sidesteps that entirely."""
    app = QApplication.instance()
    tokens = app.property(_ACTIVE_TOKENS_PROPERTY) if app else None
    if isinstance(tokens, dict):
        value = tokens.get(key)
        if isinstance(value, str):
            return QColor(value)
    return QColor(fallback)


def brand_gradient(rect: QRect | QRectF) -> QLinearGradient:
    """Diagonal blue -> purple gradient matching the app logo - or a
    plugin-contributed ThemePalette's own accent_blue/accent_purple, when
    one is the active palette (see _active_accent_colors())."""
    blue, purple = _active_accent_colors()
    gradient = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomRight()))
    gradient.setColorAt(0.0, QColor(blue))
    gradient.setColorAt(1.0, QColor(purple))
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
    blur: float = 20.0,
    y_offset: float = 4.0,
    alpha: int = 70,
) -> None:
    """Hand-paints a soft shadow behind `rect` for delegate-painted content
    (QGraphicsDropShadowEffect only applies to real QWidgets - see
    `apply_elevation()` - so a list/grid row painted inside
    QStyledItemDelegate.paint() has to fake elevation this way instead):
    many thin, progressively fainter rounded-rect *annuli*, offset
    slightly downward, filled directly with the painter already in hand -
    no QPixmap, no caching.

    Each ring is subtracted from the next-larger one (QPainterPath.
    subtracted()) so every pixel is painted by exactly one ring, never
    more - an earlier version filled full overlapping rounded rects
    instead, which looked reasonable at a glance but was a real bug: with
    ~20 overlapping semi-transparent fills stacked via normal source-over
    blending, the area right next to the card received *all* of them
    compounded, not just the one ring's intended alpha - the result was a
    thick, near-opaque dark blob hugging the card instead of a soft
    gradient (visibly, not subtly, wrong - reported directly against a
    screenshot).

    Two other approaches were tried and reverted before landing here: a
    real Gaussian blur via a throwaway QGraphicsScene +
    QGraphicsDropShadowEffect (segfaulted when painted from inside a
    QStyledItemDelegate.paint() call), and rendering the ring-based fill
    once into a `functools.lru_cache`-held QPixmap and blitting it
    thereafter (also crashed - a long-lived cache of Qt/C++-backed QPixmap
    objects reused across many separate paint sessions is exactly the kind
    of thing that can go wrong in ways that don't reproduce reliably).
    Plain per-call QPainterPath fills are the boring, proven-safe pattern
    already used everywhere else in this file - slightly more CPU per
    paint, never crashes."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)

    base_rect = QRectF(rect).translated(0, y_offset)
    rings = max(8, int(blur))
    inner_path: QPainterPath | None = None
    for i in range(1, rings + 1):
        t = i / rings  # ~0 (innermost, near-opaque) -> 1.0 (outermost, faintest)
        spread = t * blur
        # Quadratic falloff (not linear) - closer to how a real blur's
        # density actually tapers off, and it's what keeps the rings from
        # reading as discrete steps.
        ring_alpha = int(alpha * (1 - t) ** 2)
        outer_rect = base_rect.adjusted(-spread, -spread, spread, spread)
        outer_path = QPainterPath()
        outer_path.addRoundedRect(outer_rect, radius + spread, radius + spread)
        band = outer_path if inner_path is None else outer_path.subtracted(inner_path)
        if ring_alpha > 0:
            painter.fillPath(band, QColor(10, 14, 30, ring_alpha))
        inner_path = outer_path
    painter.restore()
