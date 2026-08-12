"""Paints a project row: icon, name, path subtitle, category chips, pin star.

`display_mode` ("row" for the list view, "tile" for the Phase 2 grid view) is
a hook so both views reuse this same delegate class instead of duplicating
paint logic — see ui/views/builtin.py, which builds one instance per mode.

This delegate paints everything itself (icon, text, selection background),
which means the QListView::item QSS selectors in theme/styles/*.qss don't
apply here (a custom delegate.paint() bypasses the style's normal item
drawing) — the selection/hover colors below are the ones that actually
render, and are kept visually consistent with the sidebar's QSS-driven
selection gradient by using the same brand colors.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from myapps.core.project_manager import ProjectManager
from myapps.ui.models.project_list_model import CategoriesRole, PinnedRole, ProjectPathRole
from myapps.ui.theme import brand

ROW_HEIGHT = 60
ICON_SIZE = 34
PADDING = 12
ROW_RADIUS = 10

TILE_SIZE = QSize(168, 164)
TILE_RADIUS = 12
TILE_MAX_CHIPS = 2

PIN_COLOR = QColor(brand.PIN_COLOR)
DEFAULT_CHIP_COLOR = QColor(brand.ACCENT_BLEND)


def _brand_gradient(rect: QRect) -> QLinearGradient:
    """Diagonal blue -> purple gradient matching the app logo, used for the
    folder icon glyph and for selection backgrounds."""
    gradient = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomRight()))
    gradient.setColorAt(0.0, QColor(brand.ACCENT_BLUE))
    gradient.setColorAt(1.0, QColor(brand.ACCENT_PURPLE))
    return gradient


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
            painter.fillPath(bg_path, _brand_gradient(rect))
            text_color = QColor("#ffffff")
            subtitle_color = QColor(255, 255, 255, 200)
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
        self._paint_folder_icon(painter, icon_rect)

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
        if selected:
            painter.fillPath(bg_path, _brand_gradient(rect))
            text_color = QColor("#ffffff")
        elif hovered:
            painter.fillPath(bg_path, option.palette.alternateBase())
            text_color = option.palette.text().color()
        else:
            text_color = option.palette.text().color()

        icon_rect = QRect(rect.center().x() - 24, rect.top() + 12, 48, 48)
        self._paint_folder_icon(painter, icon_rect)

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

        category_ids = index.data(CategoriesRole) or []
        self._paint_category_chips(
            painter,
            QRect(rect.left() + 4, rect.top() + 90, rect.width() - 8, 44),
            category_ids,
            on_gradient=selected,
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
        return category.name if category else "?"

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
    def _paint_folder_icon(painter: QPainter, rect: QRect) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        icon_rect = rect.adjusted(0, 2, 0, 0)
        path = QPainterPath()
        path.addRoundedRect(icon_rect, 8, 8)
        painter.fillPath(path, _brand_gradient(icon_rect))
        # A thin lighter top edge to suggest a folder tab / subtle depth.
        highlight = QPainterPath()
        highlight.addRoundedRect(icon_rect.adjusted(0, 0, 0, -int(icon_rect.height() * 0.7)), 8, 8)
        tab_color = QColor(255, 255, 255, 50)
        painter.fillPath(highlight, tab_color)
        painter.restore()
