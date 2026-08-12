"""'Open With…' dialog: pick which detected/manual editor to open a project
in, optionally setting it as that project's default, plus an "Add custom
editor…" escape hatch and an "editor not found" flow linking to downloads.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from myapps.editors.catalog import CATALOG_BY_ID, SUGGESTED_OPEN_SOURCE_IDS
from myapps.editors.registry import EditorRegistry


class EditorPickerDialog(QDialog):
    def __init__(self, registry: EditorRegistry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Open With…")
        self.setMinimumWidth(360)
        self._registry = registry

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        self._reload()
        layout.addWidget(self._list)

        self._set_default_checkbox = QCheckBox("Set as default editor for this project")
        layout.addWidget(self._set_default_checkbox)

        btn_row = QHBoxLayout()
        add_custom_btn = QPushButton("Add Custom Editor…")
        refresh_btn = QPushButton("Refresh Detection")
        not_found_btn = QPushButton("Editor Not Listed?")
        add_custom_btn.clicked.connect(self._add_custom)
        refresh_btn.clicked.connect(self._refresh)
        not_found_btn.clicked.connect(self._show_not_found_help)
        for b in (add_custom_btn, refresh_btn, not_found_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._list.itemSelectionChanged.connect(
            lambda: self._ok_button.setEnabled(bool(self._list.currentItem()))
        )
        self._ok_button.setEnabled(False)

    def _reload(self) -> None:
        self._list.clear()
        editors = self._registry.list_editors()
        if not editors:
            placeholder = QListWidgetItem("No editors detected — try Refresh or Add Custom")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list.addItem(placeholder)
            return
        for editor in editors:
            suffix = " (manual)" if editor.kind == "manual" else ""
            item = QListWidgetItem(f"{editor.display_name}{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, editor.id)
            self._list.addItem(item)

    def _refresh(self) -> None:
        self._registry.refresh()
        self._reload()

    def _add_custom(self) -> None:
        exe_path, _ = QFileDialog.getOpenFileName(self, "Select Editor Executable")
        if not exe_path:
            return
        name, ok = QInputDialog.getText(self, "Editor Name", "Display name:")
        if ok and name.strip():
            self._registry.add_manual_editor(name.strip(), exe_path)
            self._reload()

    def _show_not_found_help(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Install an Editor")
        layout = QVBoxLayout(dialog)
        layout.addWidget(
            QLabel(
                "MyAppsLibrary doesn't auto-install editors yet.\n"
                "Pick one below to open its download page, then use "
                "'Refresh Detection' once it's installed.\n\n"
                "Suggested open-source editors:"
            )
        )
        for editor_id in SUGGESTED_OPEN_SOURCE_IDS:
            entry = CATALOG_BY_ID.get(editor_id)
            if not entry:
                continue
            btn = QPushButton(entry.display_name)
            btn.clicked.connect(
                lambda _, url=entry.download_url: QDesktopServices.openUrl(QUrl(url))
            )
            layout.addWidget(btn)
        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_buttons.rejected.connect(dialog.reject)
        close_buttons.accepted.connect(dialog.accept)
        layout.addWidget(close_buttons)
        dialog.exec()

    def selected_editor_id(self) -> str | None:
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def should_set_as_default(self) -> bool:
        return self._set_default_checkbox.isChecked()
