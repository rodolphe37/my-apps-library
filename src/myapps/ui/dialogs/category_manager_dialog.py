"""Dialog for creating/renaming/deleting categories, and (from the project
context menu) editing which categories a specific project belongs to."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from myapps.core.models import Project
from myapps.core.project_manager import ProjectManager
from myapps.i18n import tr
from myapps.ui.dialogs.icon_picker_dialog import IconPickerDialog


class CategoryManagerDialog(QDialog):
    """Manage the global category list (add / rename / delete / icon)."""

    def __init__(
        self,
        project_manager: ProjectManager,
        parent: QWidget | None = None,
        plugin_manager=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.manage_categories.title"))
        self.setMinimumSize(360, 400)
        self._pm = project_manager
        self._plugins = plugin_manager

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        layout.addWidget(self._list)
        self._reload()

        btn_row = QHBoxLayout()
        add_btn = QPushButton(tr("dialog.manage_categories.add"))
        rename_btn = QPushButton(tr("dialog.manage_categories.rename"))
        icon_btn = QPushButton(tr("dialog.manage_categories.icon"))
        delete_btn = QPushButton(tr("dialog.manage_categories.delete"))
        add_btn.clicked.connect(self._add)
        rename_btn.clicked.connect(self._rename)
        icon_btn.clicked.connect(self._choose_icon)
        delete_btn.clicked.connect(self._delete)
        for b in (add_btn, rename_btn, icon_btn, delete_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _reload(self) -> None:
        self._list.clear()
        for category in self._pm.list_categories():
            label = f"{category.icon}  {category.name}" if category.icon else category.name
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self._list.addItem(item)

    def _choose_icon(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        category_id = item.data(Qt.ItemDataRole.UserRole)
        category = self._pm.get_category(category_id)
        if category is None:
            return
        plugin_packs = self._plugins.collect_icon_packs() if self._plugins else []
        dialog = IconPickerDialog(plugin_packs, category.icon, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._pm.set_category_icon(category_id, dialog.selected_icon())
            self._reload()

    def _add(self) -> None:
        name, ok = QInputDialog.getText(
            self, tr("dialog.new_category.title"), tr("dialog.new_category.label")
        )
        if ok and name.strip():
            self._pm.add_category(name.strip())
            self._reload()

    def _rename(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        new_name, ok = QInputDialog.getText(
            self,
            tr("dialog.rename_category.title"),
            tr("dialog.rename_category.label"),
            text=item.text(),
        )
        if ok and new_name.strip():
            self._pm.rename_category(item.data(Qt.ItemDataRole.UserRole), new_name.strip())
            self._reload()

    def _delete(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        confirm = QMessageBox.question(
            self,
            tr("dialog.delete_category.title"),
            tr("dialog.delete_category.body", name=item.text()),
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._pm.remove_category(item.data(Qt.ItemDataRole.UserRole))
            self._reload()


class ProjectCategoryPickerDialog(QDialog):
    """Checkbox list to edit a single project's category assignments."""

    def __init__(
        self, project: Project, project_manager: ProjectManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.project_categories.title", project_name=project.name))
        self._pm = project_manager
        self._project = project

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        for category in self._pm.list_categories():
            item = QListWidgetItem(category.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = category.id in project.categories
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self._list.addItem(item)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_category_ids(self) -> list[str]:
        return [
            self._list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self._list.count())
            if self._list.item(row).checkState() == Qt.CheckState.Checked
        ]


class BulkCategoryPickerDialog(QDialog):
    """Checkbox list to edit multiple projects' category assignments at
    once — the multi-select companion to ProjectCategoryPickerDialog.

    Each checkbox starts tri-state: checked if every selected project
    already has that category, unchecked if none do, partially-checked if
    it's a mix. A box left partially-checked is left untouched on apply();
    only boxes the user explicitly ticks or clears are added to/removed
    from every selected project — this is the only sane semantic for
    "set categories" across a heterogeneous selection (a plain overwrite
    would silently wipe categories some projects already had that others
    in the selection didn't).
    """

    def __init__(
        self,
        projects: list[Project],
        project_manager: ProjectManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        n = len(projects)
        title_key = (
            "dialog.bulk_categories.title.one" if n == 1 else "dialog.bulk_categories.title.other"
        )
        self.setWindowTitle(tr(title_key, n=n))
        self._pm = project_manager
        self._projects = projects

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr("dialog.bulk_categories.hint")))

        self._list = QListWidget()
        for category in self._pm.list_categories():
            item = QListWidgetItem(category.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            member_count = sum(1 for p in projects if category.id in p.categories)
            if member_count == 0:
                state = Qt.CheckState.Unchecked
            elif member_count == len(projects):
                state = Qt.CheckState.Checked
            else:
                state = Qt.CheckState.PartiallyChecked
            item.setCheckState(state)
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self._list.addItem(item)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def apply(self) -> None:
        """Call after exec() == Accepted. Applies every explicit
        check/uncheck across all selected projects in a single pass per
        project (never overwrites a category left partially-checked)."""
        updated: dict[str, set[str]] = {p.id: set(p.categories) for p in self._projects}
        for row in range(self._list.count()):
            item = self._list.item(row)
            state = item.checkState()
            if state == Qt.CheckState.PartiallyChecked:
                continue
            category_id = item.data(Qt.ItemDataRole.UserRole)
            for project in self._projects:
                if state == Qt.CheckState.Checked:
                    updated[project.id].add(category_id)
                else:
                    updated[project.id].discard(category_id)

        for project in self._projects:
            new_categories = sorted(updated[project.id])
            if set(new_categories) != set(project.categories):
                self._pm.set_categories(project.id, new_categories)
