"""Dialog: pick a folder, optionally rename it, and assign categories."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from myapps.core.project_manager import ProjectManager


class AddProjectDialog(QDialog):
    def __init__(self, project_manager: ProjectManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Project")
        self.setMinimumWidth(420)
        self._pm = project_manager
        self._selected_path: str | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Choose a project folder…")
        self._path_edit.textChanged.connect(self._on_path_changed)
        form.addRow("Folder:", self._path_edit)

        browse_row = QWidget()
        browse_layout = QHBoxLayout(browse_row)
        browse_layout.setContentsMargins(0, 0, 0, 0)
        browse_button = QPushButton("Browse…")
        browse_button.clicked.connect(self._browse)
        browse_layout.addWidget(browse_button)
        browse_layout.addStretch()
        form.addRow("", browse_row)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Defaults to folder name")
        form.addRow("Display name:", self._name_edit)

        layout.addWidget(QLabel("Categories:"))
        self._category_list = QListWidget()
        self._category_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        for category in self._pm.list_categories():
            item = QListWidgetItem(category.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self._category_list.addItem(item)
        layout.addWidget(self._category_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")
        if folder:
            self._path_edit.setText(folder)

    def _on_path_changed(self, text: str) -> None:
        self._selected_path = text.strip() or None
        self._ok_button.setEnabled(bool(self._selected_path))
        if self._selected_path and not self._name_edit.text():
            self._name_edit.setPlaceholderText(Path(self._selected_path).name)

    def result_data(self) -> tuple[str, str | None, list[str]] | None:
        """Returns (path, name_or_None, category_ids) if accepted, else None."""
        if not self._selected_path:
            return None
        categories = [
            self._category_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self._category_list.count())
            if self._category_list.item(row).checkState() == Qt.CheckState.Checked
        ]
        name = self._name_edit.text().strip() or None
        return self._selected_path, name, categories
