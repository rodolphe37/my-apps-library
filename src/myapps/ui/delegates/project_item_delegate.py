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

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from myapps.core.project_manager import ProjectManager
from myapps.ui.models.project_list_model import (
    CategoriesRole,
    IconRole,
    PinnedRole,
    ProjectPathRole,
)
from myapps.ui.theme import brand
from myapps.ui.theme.shapes import paint_folder_icon, paint_soft_shadow

ROW_HEIGHT = 60
ICON_SIZE = 34
PADDING = 12
ROW_RADIUS = 12

TILE_SIZE = QSize(168, 164)
TILE_RADIUS = 14
TILE_MAX_CHIPS = 2

PIN_COLOR = QColor(brand.PIN_COLOR)
DEFAULT_CHIP_COLOR = QColor(brand.ACCENT_BLEND)
SELECTION_BORDER_COLOR = QColor(brand.ACCENT_BLEND)
SELECTION_BORDER_WIDTH = 2


def _paint_selection_border(painter: QPainter, bg_path: QPainterPath) -> None:
    """Selected rows/tiles get a soft accent-tinted fill plus an
    accent-colored outline - not an opaque fill - so the row's own colors
    (icon gradient, category chip tints) stay readable instead of being
    washed out by a solid background behind them."""
    painter.save()
    tint = QColor(SELECTION_BORDER_COLOR)
    tint.setAlpha(28)
    painter.fillPath(bg_path, tint)
    pen = QPen(SELECTION_BORDER_COLOR, SELECTION_BORDER_WIDTH)
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
        if selected:
            _paint_selection_border(painter, bg_path)
            text_color = option.palette.text().color()
            subtitle_color = option.palette.placeholderText().color()
        elif hovered:
            painter.fillPath(bg_path, option.palette.alternateBase())
            text_color = option.palette.text().color()
            subtitle_color = option.palette.placeholderText().color()
        else:
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

        name_rect = QRect(text_left, rect.top() + 8, rect.width() - text_left - PADDING, 20)
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
        path_rect = QRect(text_left, rect.top() + 30, rect.width() - text_left - PADDING, 18)
        elided_path = QFontMetrics(font).elidedText(
            path, Qt.TextElideMode.ElideMiddle, path_rect.width()
        )
        painter.drawText(path_rect, Qt.AlignmentFlag.AlignVCenter, elided_path)

        if pinned:
            self._paint_pin_star(
                painter, QRect(rect.right() - PADDING - 16, rect.top(), 16, rect.height())
            )

        painter.restore()

    def _paint_tile(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        rect = option.rect.adjusted(6, 6, -6, -6)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, TILE_RADIUS, TILE_RADIUS)
        if selected or hovered:
            # Tiles read as raised cards, so a hovered/selected one gets a
            # hand-painted soft shadow (see shapes.paint_soft_shadow's
            # docstring for why this can't just be a QGraphicsDropShadowEffect
            # - tiles are painted by this delegate, not real QWidgets).
            paint_soft_shadow(painter, rect, TILE_RADIUS)
        if selected:
            _paint_selection_border(painter, bg_path)
            text_color = option.palette.text().color()
        elif hovered:
            painter.fillPath(bg_path, option.palette.base())
            text_color = option.palette.text().color()
        else:
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

        x = area.left()
        y = area.top()
        row_height = metrics.height() + 6
        for label in labels:
            chip_width = min(metrics.horizontalAdvance(label) + 14, area.width())
            if x + chip_width > area.right() and x != area.left():
                x = area.left()
                y += row_height + 3
            if y + row_height > area.bottom():
                break
            chip_rect = QRect(x, y, chip_width, row_height)
            self._paint_one_chip(painter, chip_rect, label, on_gradient)
            x += chip_width + 4

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
            chip_bg = QColor(DEFAULT_CHIP_COLOR)
            chip_bg.setAlpha(38)
            text_color = QColor(DEFAULT_CHIP_COLOR)
        painter.fillPath(path, chip_bg)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

    @staticmethod
    def _paint_pin_star(painter: QPainter, rect: QRect) -> None:
        painter.save()
        painter.setPen(PIN_COLOR)
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
