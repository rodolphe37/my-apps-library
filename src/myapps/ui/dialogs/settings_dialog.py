"""Preferences dialog: theme mode and global default editor."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
    QWidget,
)

from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings_manager: SettingsManager,
        editor_registry: EditorRegistry,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(360)
        self._settings = settings_manager
        self._registry = editor_registry

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Follow System", "system")
        self._theme_combo.addItem("Light", "light")
        self._theme_combo.addItem("Dark", "dark")
        current_theme = settings_manager.settings.theme_mode
        self._theme_combo.setCurrentIndex(max(0, self._theme_combo.findData(current_theme)))
        form.addRow("Theme:", self._theme_combo)

        self._editor_combo = QComboBox()
        self._editor_combo.addItem("None", None)
        for editor in editor_registry.list_editors():
            self._editor_combo.addItem(editor.display_name, editor.id)
        current_editor = settings_manager.settings.global_default_editor_id
        idx = self._editor_combo.findData(current_editor)
        self._editor_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("Default editor:", self._editor_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        self._settings.set(
            theme_mode=self._theme_combo.currentData(),
            global_default_editor_id=self._editor_combo.currentData(),
        )
        self.accept()
