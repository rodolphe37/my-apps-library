"""Dialog for creating/renaming/deleting categories, and (from the project
context menu) editing which categories a specific project belongs to."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
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


class CategoryManagerDialog(QDialog):
    """Manage the global category list (add / rename / delete)."""

    def __init__(self, project_manager: ProjectManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.manage_categories.title"))
        self.setMinimumSize(360, 400)
        self._pm = project_manager

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        layout.addWidget(self._list)
        self._reload()

        btn_row = QHBoxLayout()
        add_btn = QPushButton(tr("dialog.manage_categories.add"))
        rename_btn = QPushButton(tr("dialog.manage_categories.rename"))
        delete_btn = QPushButton(tr("dialog.manage_categories.delete"))
        add_btn.clicked.connect(self._add)
        rename_btn.clicked.connect(self._rename)
        delete_btn.clicked.connect(self._delete)
        for b in (add_btn, rename_btn, delete_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _reload(self) -> None:
        self._list.clear()
        for category in self._pm.list_categories():
            item = QListWidgetItem(category.name)
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self._list.addItem(item)

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
            self, tr("dialog.rename_category.title"), tr("dialog.rename_category.label"),
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
