"""Paints a project row: icon, name, path subtitle, category chips, pin star.

`display_mode` ("row" for the list view, "tile" for the Phase 2 grid view) is
a hook so both views reuse this same delegate class instead of duplicating
paint logic — see ui/views/builtin.py, which builds one instance per mode.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from myapps.core.project_manager import ProjectManager
from myapps.ui.models.project_list_model import CategoriesRole, PinnedRole, ProjectPathRole

ROW_HEIGHT = 56
ICON_SIZE = 32
PADDING = 10

TILE_SIZE = QSize(168, 160)
TILE_MAX_CHIPS = 2
PIN_COLOR = QColor("#f5a623")
DEFAULT_CHIP_COLOR = QColor("#8e8e93")


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
        if self.display_mode == "tile":
            self._paint_tile(painter, option, index)
        else:
            self._paint_row(painter, option, index)

    def _paint_row(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        rect = option.rect

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
            subtitle_color = text_color
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

        name_rect = QRect(text_left, rect.top() + 6, rect.width() - text_left - PADDING, 20)
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
        path_rect = QRect(text_left, rect.top() + 28, rect.width() - text_left - PADDING, 18)
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(6, 6, -6, -6)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected:
            bg_path = QPainterPath()
            bg_path.addRoundedRect(rect, 10, 10)
            painter.fillPath(bg_path, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        elif hovered:
            bg_path = QPainterPath()
            bg_path.addRoundedRect(rect, 10, 10)
            hover_color = QColor(option.palette.text().color())
            hover_color.setAlpha(18)
            painter.fillPath(bg_path, hover_color)
            text_color = option.palette.text().color()
        else:
            text_color = option.palette.text().color()

        icon_rect = QRect(rect.center().x() - 24, rect.top() + 10, 48, 48)
        self._paint_folder_icon(painter, icon_rect)

        pinned = bool(index.data(PinnedRole))
        if pinned:
            self._paint_pin_star(painter, QRect(rect.right() - 20, rect.top() + 2, 16, 16))

        name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        name_rect = QRect(rect.left() + 4, rect.top() + 64, rect.width() - 8, 20)
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
            painter, QRect(rect.left() + 4, rect.top() + 88, rect.width() - 8, 44), category_ids
        )

        painter.restore()

    def _paint_category_chips(
        self, painter: QPainter, area: QRect, category_ids: list[str]
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
            self._paint_one_chip(painter, chip_rect, label)
            x += chip_width + 4

    def _chip_label(self, category_id: str) -> str:
        category = self._pm.get_category(category_id)
        return category.name if category else "?"

    @staticmethod
    def _paint_one_chip(painter: QPainter, rect: QRect, label: str) -> None:
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        chip_bg = QColor(DEFAULT_CHIP_COLOR)
        chip_bg.setAlpha(60)
        painter.fillPath(path, chip_bg)
        painter.setPen(DEFAULT_CHIP_COLOR)
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
        path = QPainterPath()
        path.addRoundedRect(rect.adjusted(0, 2, 0, 0), 4, 4)
        painter.fillPath(path, QColor("#5ac8fa"))
        painter.restore()
