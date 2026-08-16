"""Dialog: pick a folder, optionally rename it, and assign categories."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from myapps.core.project_manager import ProjectManager
from myapps.i18n import tr
from myapps.ui.widgets.dialog_buttons import standard_button_box
from myapps.ui.widgets.flow_layout import FlowLayout


class AddProjectDialog(QDialog):
    def __init__(self, project_manager: ProjectManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.add_project.title"))
        self.setMinimumWidth(440)
        self._pm = project_manager
        self._selected_path: str | None = None
        self._category_chips: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(18)

        layout.addLayout(self._build_folder_field())

        name_field, self._name_edit = self._build_field(
            tr("dialog.add_project.name_label"), tr("dialog.add_project.name_placeholder")
        )
        layout.addLayout(name_field)

        layout.addLayout(self._build_categories_field())
        layout.addStretch(1)

        buttons = standard_button_box(
            QDialogButtonBox.StandardButton.Ok, QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)

    @staticmethod
    def _build_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _build_field(self, label_text: str, placeholder: str) -> tuple[QVBoxLayout, QLineEdit]:
        field_layout = QVBoxLayout()
        field_layout.setSpacing(6)
        field_layout.addWidget(self._build_label(label_text))
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        field_layout.addWidget(edit)
        return field_layout, edit

    def _build_folder_field(self) -> QVBoxLayout:
        field_layout = QVBoxLayout()
        field_layout.setSpacing(6)
        field_layout.addWidget(self._build_label(tr("dialog.add_project.folder_label")))

        row = QHBoxLayout()
        row.setSpacing(8)
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText(tr("dialog.add_project.folder_placeholder"))
        self._path_edit.textChanged.connect(self._on_path_changed)
        row.addWidget(self._path_edit, 1)

        browse_button = QPushButton(tr("dialog.add_project.browse"))
        browse_button.clicked.connect(self._browse)
        row.addWidget(browse_button)
        field_layout.addLayout(row)
        return field_layout

    def _build_categories_field(self) -> QVBoxLayout:
        field_layout = QVBoxLayout()
        field_layout.setSpacing(8)
        field_layout.addWidget(self._build_label(tr("dialog.add_project.categories_label")))

        chip_area = QWidget()
        chip_flow = FlowLayout(chip_area, h_spacing=8, v_spacing=8)
        for category in self._pm.list_categories():
            label = f"{category.icon}  {category.name}" if category.icon else category.name
            chip = QPushButton(label)
            chip.setObjectName("CategoryChipToggle")
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip_flow.addWidget(chip)
            self._category_chips[category.id] = chip
        field_layout.addWidget(chip_area)
        return field_layout

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("dialog.add_project.browse_title"))
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
            category_id for category_id, chip in self._category_chips.items() if chip.isChecked()
        ]
        name = self._name_edit.text().strip() or None
        return self._selected_path, name, categories
