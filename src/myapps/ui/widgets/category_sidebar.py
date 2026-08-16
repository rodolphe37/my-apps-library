"""Left sidebar: All / Uncategorized / each category, for filtering the
project list. Emits `category_selected(category_id_or_None)`; a sentinel
string "__all__" is translated to None-with-no-filter by main_window.

Also accepts drops of a project dragged from the list/grid view (see
ui/models/project_list_model.py's PROJECT_ID_MIME_TYPE and
ui/views/project_list_view.py's drag-enabled setup): dropping a project onto
a category here *replaces* its categories with just that one - a "move into
folder" semantic, distinct from the checkbox-based multi-category assignment
in Project > Edit Categories…, which is still there for tagging a project
into several categories at once.

Rows are painted by `_CategorySidebarDelegate`, not plain QListWidgetItem
text - a label left-aligned and a muted count right-aligned in the *same*
row needs two independently-positioned text runs, which a single
QListWidgetItem string can't express. Same tradeoff as
delegates/project_item_delegate.py: this bypasses the QSS `::item` selectors
in theme/styles/*.qss, so the selection/hover colors below are the ones that
actually render.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFontMetrics,
    QPainter,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from myapps.constants import UNCATEGORIZED_ID
from myapps.core.events import event_bus
from myapps.core.project_manager import ProjectManager
from myapps.i18n import tr
from myapps.ui.models.project_list_model import PROJECT_ID_MIME_TYPE
from myapps.ui.theme import brand
from myapps.ui.theme.shapes import active_token, brand_gradient

ALL_ITEM_ID = "__all__"

# Custom roles, past Qt's reserved built-in ones and past the plain UserRole
# already used for the filter id (ALL_ITEM_ID | UNCATEGORIZED_ID | category
# id | None for a header row).
_COUNT_ROLE = Qt.ItemDataRole.UserRole + 1
_HEADER_ROLE = Qt.ItemDataRole.UserRole + 2

_ROW_HEIGHT = 34
_HEADER_HEIGHT = 26


class _CategorySidebarDelegate(QStyledItemDelegate):
    """Paints every sidebar row: a header ("Library"/"Categories" - muted,
    uppercase, no count) or an entry (icon+label left, count right-aligned
    in a muted tone; the active "All"/category gets the full brand gradient
    with white text, matching the accent used everywhere else selection is
    shown - see project_item_delegate.py)."""

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:  # noqa: N802
        height = _HEADER_HEIGHT if index.data(_HEADER_ROLE) else _ROW_HEIGHT
        return QSize(option.rect.width(), height)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        label = index.data(Qt.ItemDataRole.DisplayRole) or ""

        if index.data(_HEADER_ROLE):
            font = painter.font()
            font.setBold(True)
            font.setPointSizeF(font.pointSizeF() * 0.78)
            painter.setFont(font)
            painter.setPen(option.palette.placeholderText().color())
            text_rect = option.rect.adjusted(14, 0, -8, 0)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, label.upper())
            painter.restore()
            return

        rect = QRect(option.rect).adjusted(6, 2, -6, -2)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 9, 9)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected:
            painter.fillPath(path, brand_gradient(rect))
            text_color = QColor("#ffffff")
            count_color = QColor(255, 255, 255, 215)
        else:
            if hovered:
                # active_token(), not option.palette.alternateBase() - a
                # fill color specifically can't trust option.palette once a
                # global QSS is active (CategorySidebar's own
                # `background-color: transparent` rule can bleed into it).
                # See shapes.active_token()'s own docstring.
                painter.fillPath(path, active_token("surface_alt", brand.LIGHT_SURFACE_ALT))
            text_color = option.palette.text().color()
            count_color = option.palette.placeholderText().color()

        font = painter.font()
        font.setBold(selected)
        painter.setFont(font)
        metrics = QFontMetrics(font)

        count = index.data(_COUNT_ROLE)
        count_text = "" if count is None else str(count)
        count_width = metrics.horizontalAdvance(count_text) if count_text else 0

        label_width = rect.width() - 20 - count_width - (8 if count_text else 0)
        label_rect = QRect(rect.left() + 10, rect.top(), label_width, rect.height())
        painter.setPen(text_color)
        painter.drawText(
            label_rect,
            Qt.AlignmentFlag.AlignVCenter,
            metrics.elidedText(label, Qt.TextElideMode.ElideRight, label_rect.width()),
        )

        if count_text:
            count_rect = QRect(
                rect.right() - 10 - count_width, rect.top(), count_width, rect.height()
            )
            painter.setPen(count_color)
            painter.drawText(
                count_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, count_text
            )

        painter.restore()


class CategorySidebar(QListWidget):
    filter_changed = Signal(str)  # ALL_ITEM_ID | UNCATEGORIZED_ID | category_id
    project_recategorized = Signal(str, str)  # project_name, category_label (for status bar)

    def __init__(self, project_manager: ProjectManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CategorySidebar")
        self._pm = project_manager
        self.setFrameShape(QListWidget.Shape.NoFrame)
        self.setAcceptDrops(True)
        self.setItemDelegate(_CategorySidebarDelegate(self))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)  # so the delegate's ':hover' fires
        # A single-column list that should never need to scroll sideways -
        # long labels elide instead (see the delegate's paint()). Without
        # this, sizeHint()'s use of option.rect.width() (0 during the very
        # first layout pass, before the view has a real width) can make Qt
        # briefly think content is wider than the viewport and show a
        # horizontal scrollbar that then never goes away.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._refresh()
        self.currentItemChanged.connect(self._on_current_changed)

        event_bus.category_added.connect(self._refresh)
        event_bus.category_updated.connect(self._refresh)
        event_bus.category_removed.connect(self._refresh)
        event_bus.project_added.connect(self._refresh)
        event_bus.project_removed.connect(self._refresh)
        event_bus.project_updated.connect(self._refresh)

    def _refresh(self, *_args) -> None:
        previously_selected = self._current_filter_id()
        self.blockSignals(True)
        self.clear()

        all_item = QListWidgetItem(tr("sidebar.all"))
        all_item.setData(Qt.ItemDataRole.UserRole, ALL_ITEM_ID)
        all_item.setData(_COUNT_ROLE, len(self._pm.list_projects()))
        self.addItem(all_item)

        categories = self._pm.list_categories()
        if categories:
            self.addItem(self._make_section_header(tr("sidebar.categories_header")))
        for category in categories:
            # category.name is user data, never translated.
            count = len(self._pm.projects_in_category(category.id))
            display_name = f"{category.icon} {category.name}" if category.icon else category.name
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            item.setData(_COUNT_ROLE, count)
            self.addItem(item)

        uncategorized_item = QListWidgetItem(f"+ {tr('sidebar.uncategorized')}")
        uncategorized_item.setData(Qt.ItemDataRole.UserRole, UNCATEGORIZED_ID)
        uncategorized_item.setData(_COUNT_ROLE, len(self._pm.projects_in_category(None)))
        self.addItem(uncategorized_item)

        self.blockSignals(False)
        self._select_filter_id(previously_selected or ALL_ITEM_ID)

    @staticmethod
    def _make_section_header(label: str) -> QListWidgetItem:
        """A purely visual group label ("Categories") sitting above the
        category rows - not a real filter target. `Qt.ItemFlag.NoItemFlags`
        makes it neither selectable nor enabled, so it can never become
        `currentItem()` (click or keyboard) and _select_filter_id()/
        _current_filter_id() never have to special-case it; `_HEADER_ROLE`
        is what `_CategorySidebarDelegate` actually keys its painting off
        of."""
        item = QListWidgetItem(label)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setData(_HEADER_ROLE, True)
        return item

    def _current_filter_id(self) -> str | None:
        item = self.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _select_filter_id(self, filter_id: str) -> None:
        for row in range(self.count()):
            item = self.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == filter_id:
                self.setCurrentItem(item)
                return
        if self.count():
            self.setCurrentRow(0)

    def _on_current_changed(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if not current:
            return
        filter_id = current.data(Qt.ItemDataRole.UserRole)
        if filter_id is None:
            # The "Categories" section header (see _make_section_header) -
            # NoItemFlags keeps it out of normal mouse/keyboard selection,
            # but Qt's own setCurrentItem() API can still land here (e.g.
            # restoring a previous selection mid-refresh), and that must
            # never turn into "filter by category=None" (the Uncategorized
            # semantic). Bounce back to wherever selection was, or "All" if
            # there's nowhere to bounce back to.
            if previous:
                self.setCurrentItem(previous)
            else:
                self._select_filter_id(ALL_ITEM_ID)
            return
        self.filter_changed.emit(filter_id)

    # -- drag & drop (project -> category) --------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(PROJECT_ID_MIME_TYPE):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(PROJECT_ID_MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        if not event.mimeData().hasFormat(PROJECT_ID_MIME_TYPE):
            return
        target_item = self.itemAt(event.position().toPoint())
        project_id = bytes(event.mimeData().data(PROJECT_ID_MIME_TYPE)).decode("utf-8")
        if self._handle_drop(target_item, project_id):
            event.acceptProposedAction()

    def _handle_drop(self, target_item: QListWidgetItem | None, project_id: str) -> bool:
        """Applies the drop: replaces `project_id`'s categories with just the
        target category (or clears them, for "Uncategorized"). Separated from
        dropEvent() so it can be exercised directly in tests without
        constructing a real QDropEvent (fragile in PySide6 - event objects
        built in Python can crash when Qt's C++ side later reads them back).
        Returns True if the drop was handled.
        """
        if target_item is None:
            return False
        target_id = target_item.data(Qt.ItemDataRole.UserRole)
        if target_id == ALL_ITEM_ID:
            return False  # "All" isn't a real category to move into

        project = self._pm.get_project(project_id)
        if not project:
            return False

        if target_id == UNCATEGORIZED_ID:
            self._pm.set_categories(project_id, [])
            category_label = tr("sidebar.uncategorized")
        else:
            self._pm.set_categories(project_id, [target_id])
            category = self._pm.get_category(target_id)
            category_label = category.name if category else target_id

        self.project_recategorized.emit(project.name, category_label)
        return True
