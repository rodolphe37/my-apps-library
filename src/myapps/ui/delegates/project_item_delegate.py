"""Paints a project row: icon, name, path subtitle, category chips, pin star.

`display_mode` ("row" for the list view, "tile" for the Phase 2 grid view) is
a hook so both views reuse this same delegate class instead of duplicating
paint logic - see ui/views/builtin.py, which builds one instance per mode.

This delegate paints everything itself (icon, text, selection outline),
which means the QListView::item QSS selectors in theme/styles/*.qss don't
apply here (a custom delegate.paint() bypasses the style's normal item
drawing) - the selection/hover colors below are the ones that actually
render. Selection is an accent-colored border, not a filled background, so
a row/tile's own colors (icon gradient, category chip tints) stay readable
when selected instead of being washed out.
"""

from __future__ import annotations

from PySide6.QtCore import QDateTime, QLocale, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from myapps.core.project_manager import ProjectManager
from myapps.ui.models.project_list_model import (
    CategoriesRole,
    IconRole,
    ModifiedAtRole,
    PinnedRole,
    ProjectPathRole,
)
from myapps.ui.theme import brand
from myapps.ui.theme.shapes import active_token, paint_folder_icon, paint_soft_shadow

ROW_HEIGHT = 60
ICON_SIZE = 34
PADDING = 12
ROW_RADIUS = 12

TILE_SIZE = QSize(168, 164)
TILE_RADIUS = 14
TILE_MAX_CHIPS = 2

SELECTION_BORDER_WIDTH = 2


# Colors read fresh on every paint via shapes.active_token(), not module-level
# constants baked from brand.py at import time - two reasons: (1) a plugin-
# contributed ThemePalette can override pin_color/accent_blend, and a
# constant computed once at import would never pick that up; (2)
# option.palette can't be used for this either - see _paint_tile's own note
# on why a QSS-styled QListView's palette can't be trusted for exact colors.
def _pin_color() -> QColor:
    return active_token("pin_color", brand.PIN_COLOR)


def _chip_color() -> QColor:
    return active_token("accent_blend", brand.ACCENT_BLEND)


def _selection_color() -> QColor:
    return active_token("accent_blend", brand.ACCENT_BLEND)


def _format_row_date(mtime: float | None) -> str:
    """ "8 août"/"Aug 8"-style short date for a list row's trailing column -
    day + locale-abbreviated month, no year (rows are recent-ish projects,
    a year rarely adds information here). Empty string (not "-" or "?") on
    a missing mtime so the caller can just skip painting it entirely."""
    if mtime is None:
        return ""
    qdt = QDateTime.fromSecsSinceEpoch(int(mtime))
    return QLocale().toString(qdt.date(), "d MMM")


def _paint_selection_border(painter: QPainter, bg_path: QPainterPath) -> None:
    """Selected rows/tiles get a soft accent-tinted fill plus an
    accent-colored outline - not an opaque fill - so the row's own colors
    (icon gradient, category chip tints) stay readable instead of being
    washed out by a solid background behind them."""
    painter.save()
    tint = _selection_color()
    tint.setAlpha(28)
    painter.fillPath(bg_path, tint)
    pen = QPen(_selection_color(), SELECTION_BORDER_WIDTH)
    painter.setPen(pen)
    painter.drawPath(bg_path)
    painter.restore()


class ProjectItemDelegate(QStyledItemDelegate):
    def __init__(self, project_manager: ProjectManager, parent=None) -> None:
        super().__init__(parent)
        self._pm = project_manager
        self.display_mode = "row"  # "row" (list) | "tile" (grid)

    def sizeHint(self, option, index) -> QSize:  # noqa: N802
        if self.display_mode == "tile":
            return TILE_SIZE
        return QSize(option.rect.width(), ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.display_mode == "tile":
            self._paint_tile(painter, option, index)
        else:
            self._paint_row(painter, option, index)

    def _paint_row(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        rect = option.rect.adjusted(4, 2, -4, -2)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, ROW_RADIUS, ROW_RADIUS)
        if selected or hovered:
            # A faint lift on hover/selected, same idea as the tile's card
            # shadow but subtler - rows are denser, so a heavy shadow per
            # row would be visual noise.
            paint_soft_shadow(painter, rect, ROW_RADIUS, blur=14.0, y_offset=2.0, alpha=24)
        if selected:
            _paint_selection_border(painter, bg_path)
        elif hovered:
            # active_token(), not option.palette.alternateBase() - see
            # _paint_tile's note on why a fill color specifically can't
            # trust option.palette once a global QSS is active.
            painter.fillPath(bg_path, active_token("surface_alt", brand.LIGHT_SURFACE_ALT))
        text_color = option.palette.text().color()
        subtitle_color = option.palette.placeholderText().color()

        icon_rect = QRect(
            rect.left() + PADDING,
            rect.top() + (rect.height() - ICON_SIZE) // 2,
            ICON_SIZE,
            ICON_SIZE,
        )
        self._paint_folder_icon(painter, icon_rect, index.data(IconRole))

        text_left = icon_rect.right() + PADDING
        name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        path = index.data(ProjectPathRole) or ""
        pinned = bool(index.data(PinnedRole))
        category_ids = index.data(CategoriesRole) or []
        date_text = _format_row_date(index.data(ModifiedAtRole))

        # The trailing meta group (category chip, pin star, date) is
        # measured first so the name/path columns know how much width is
        # actually left to elide into - painted afterward, right-aligned,
        # right to left: date, then star, then chip.
        meta_font = painter.font()
        meta_font.setPointSizeF(meta_font.pointSizeF() * 0.82)
        meta_metrics = QFontMetrics(meta_font)

        date_width = meta_metrics.horizontalAdvance(date_text) if date_text else 0
        chip_label = self._chip_label(category_ids[0]) if category_ids else None
        chip_width = meta_metrics.horizontalAdvance(chip_label) + 16 if chip_label else 0
        star_width = 16 if pinned else 0

        meta_width = 0
        if date_text:
            meta_width += date_width + 12
        if pinned:
            meta_width += star_width + 8
        if chip_label:
            meta_width += chip_width + 10

        text_width = max(40, rect.width() - (text_left - rect.left()) - PADDING - meta_width)
        name_rect = QRect(text_left, rect.top() + 8, text_width, 20)
        painter.setPen(text_color)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        elided_name = QFontMetrics(font).elidedText(
            name, Qt.TextElideMode.ElideRight, name_rect.width()
        )
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter, elided_name)

        font.setBold(False)
        font.setPointSizeF(font.pointSizeF() * 0.9)
        painter.setFont(font)
        painter.setPen(subtitle_color)
        path_rect = QRect(text_left, rect.top() + 30, text_width, 18)
        elided_path = QFontMetrics(font).elidedText(
            path, Qt.TextElideMode.ElideMiddle, path_rect.width()
        )
        painter.drawText(path_rect, Qt.AlignmentFlag.AlignVCenter, elided_path)

        x = rect.right() - PADDING
        if date_text:
            date_rect = QRect(x - date_width, rect.top(), date_width, rect.height())
            painter.setFont(meta_font)
            painter.setPen(subtitle_color)
            painter.drawText(
                date_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, date_text
            )
            x -= date_width + 12
        if pinned:
            star_rect = QRect(x - star_width, rect.top(), star_width, rect.height())
            self._paint_pin_star(painter, star_rect)
            x -= star_width + 8
        if chip_label:
            chip_rect = QRect(x - chip_width, rect.center().y() - 10, chip_width, 20)
            painter.setFont(meta_font)
            self._paint_one_chip(painter, chip_rect, chip_label, on_gradient=False)

        painter.restore()

    def _paint_tile(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        rect = option.rect.adjusted(6, 6, -6, -6)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, TILE_RADIUS, TILE_RADIUS)

        # A tile's fill matches the page background at rest - only a
        # hairline border defines the card - and hover/selected add a real
        # elevation (a shadow that isn't there at rest, plus a darker
        # neutral border on hover or the accent tint+border on selected).
        #
        # active_token(), not option.palette.base()/placeholderText(): once
        # a global QSS is applied (this app always has one), Qt's style-
        # sheet cascade can recompute a widget's *effective* QPalette from
        # the stylesheet rather than leaving it as the plain app palette -
        # e.g. QListView's own `background-color: transparent` rule
        # bleeding into option.palette.base() here. See shapes.
        # active_token()'s own docstring.
        raised = selected or hovered
        if raised:
            paint_soft_shadow(painter, rect, TILE_RADIUS, blur=24.0, y_offset=4.0, alpha=36)
        painter.fillPath(bg_path, active_token("bg", brand.LIGHT_BG))
        if selected:
            _paint_selection_border(painter, bg_path)
        else:
            border_color = active_token("border", brand.LIGHT_BORDER)
            border_color.setAlpha(170 if hovered else 140)
            painter.setPen(QPen(border_color, 1))
            painter.drawPath(bg_path)
        text_color = option.palette.text().color()

        icon_rect = QRect(rect.center().x() - 24, rect.top() + 12, 48, 48)
        self._paint_folder_icon(painter, icon_rect, index.data(IconRole))

        pinned = bool(index.data(PinnedRole))
        if pinned:
            self._paint_pin_star(painter, QRect(rect.right() - 20, rect.top() + 2, 16, 16))

        name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        name_rect = QRect(rect.left() + 4, rect.top() + 66, rect.width() - 8, 20)
        painter.setPen(text_color)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            name_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            QFontMetrics(font).elidedText(name, Qt.TextElideMode.ElideRight, name_rect.width()),
        )
        font.setBold(False)
        painter.setFont(font)

        # Chips are never painted "on_gradient" style anymore now that
        # selection is an outline rather than a filled background - always
        # use the normal translucent brand-tinted chip.
        category_ids = index.data(CategoriesRole) or []
        self._paint_category_chips(
            painter,
            QRect(rect.left() + 4, rect.top() + 90, rect.width() - 8, 44),
            category_ids,
        )

        painter.restore()

    def _paint_category_chips(
        self, painter: QPainter, area: QRect, category_ids: list[str], on_gradient: bool = False
    ) -> None:
        """Tiles are centered content (icon, name, and chip(s) all sit on
        the tile's vertical axis - see the mockup this design follows), so
        each row of chips is centered within `area` too, not left-stuck.
        Labels are bucketed into width-capped rows first so each row's
        total width is known before it's painted - the only way to center
        it."""
        if not category_ids:
            return
        shown = category_ids[:TILE_MAX_CHIPS]
        overflow = len(category_ids) - len(shown)
        labels = [self._chip_label(cid) for cid in shown]
        if overflow > 0:
            labels.append(f"+{overflow}")

        font = painter.font()
        font.setPointSizeF(font.pointSizeF() * 0.78)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        row_height = metrics.height() + 6
        gap = 4

        rows: list[list[tuple[str, int]]] = [[]]
        row_width = 0
        for label in labels:
            chip_width = min(metrics.horizontalAdvance(label) + 14, area.width())
            needed_width = chip_width if not rows[-1] else row_width + gap + chip_width
            if needed_width > area.width() and rows[-1]:
                rows.append([])
                row_width = 0
            rows[-1].append((label, chip_width))
            row_width = row_width + gap + chip_width if len(rows[-1]) > 1 else chip_width

        y = area.top()
        for row in rows:
            if not row or y + row_height > area.bottom():
                break
            total_width = sum(w for _, w in row) + gap * (len(row) - 1)
            x = area.left() + max(0, (area.width() - total_width) // 2)
            for label, chip_width in row:
                chip_rect = QRect(x, y, chip_width, row_height)
                self._paint_one_chip(painter, chip_rect, label, on_gradient)
                x += chip_width + gap
            y += row_height + 3

    def _chip_label(self, category_id: str) -> str:
        category = self._pm.get_category(category_id)
        if category is None:
            return "?"
        return f"{category.icon} {category.name}" if category.icon else category.name

    @staticmethod
    def _paint_one_chip(painter: QPainter, rect: QRect, label: str, on_gradient: bool) -> None:
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        if on_gradient:
            chip_bg = QColor(255, 255, 255, 60)
            text_color = QColor("#ffffff")
        else:
            chip_bg = _chip_color()
            chip_bg.setAlpha(38)
            text_color = _chip_color()
        painter.fillPath(path, chip_bg)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

    @staticmethod
    def _paint_pin_star(painter: QPainter, rect: QRect) -> None:
        painter.save()
        painter.setPen(_pin_color())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "★")
        painter.restore()

    @staticmethod
    def _paint_folder_icon(painter: QPainter, rect: QRect, glyph: str | None = None) -> None:
        # A picked icon (built-in or plugin-contributed) is overlaid
        # centered on top of the folder shape, not a replacement for it, so
        # a project always still reads as a folder - see
        # ui/theme/shapes.py::paint_folder_icon() for the actual silhouette
        # (shared with PluginManagerDialog's generated fallback icon, so
        # the app's one "folder" shape only ever exists in one place).
        paint_folder_icon(painter, rect.adjusted(0, 2, 0, 0), glyph)
