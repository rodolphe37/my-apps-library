"""Preferences dialog: theme mode, language, and global default editor."""

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
from myapps.i18n import LanguageManager, tr, translator


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings_manager: SettingsManager,
        editor_registry: EditorRegistry,
        parent: QWidget | None = None,
        language_manager: LanguageManager | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.settings.title"))
        self.setMinimumWidth(360)
        self._settings = settings_manager
        self._registry = editor_registry
        self._language_manager = language_manager

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem(tr("dialog.settings.theme_system"), "system")
        self._theme_combo.addItem(tr("dialog.settings.theme_light"), "light")
        self._theme_combo.addItem(tr("dialog.settings.theme_dark"), "dark")
        current_theme = settings_manager.settings.theme_mode
        self._theme_combo.setCurrentIndex(max(0, self._theme_combo.findData(current_theme)))
        form.addRow(tr("dialog.settings.theme_label"), self._theme_combo)

        self._language_combo = QComboBox()
        self._language_combo.addItem(tr("dialog.settings.language_system"), "system")
        for locale in sorted(translator.available_locales()):
            self._language_combo.addItem(translator.display_name(locale), locale)
        current_language = settings_manager.settings.language
        lang_idx = self._language_combo.findData(current_language)
        self._language_combo.setCurrentIndex(lang_idx if lang_idx >= 0 else 0)
        form.addRow(tr("dialog.settings.language_label"), self._language_combo)

        self._editor_combo = QComboBox()
        self._editor_combo.addItem(tr("dialog.settings.editor_none"), None)
        for editor in editor_registry.list_editors():
            self._editor_combo.addItem(editor.display_name, editor.id)
        current_editor = settings_manager.settings.global_default_editor_id
        idx = self._editor_combo.findData(current_editor)
        self._editor_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow(tr("dialog.settings.editor_label"), self._editor_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        new_language = self._language_combo.currentData()
        self._settings.set(
            theme_mode=self._theme_combo.currentData(),
            language=new_language,
            global_default_editor_id=self._editor_combo.currentData(),
        )
        if self._language_manager is not None:
            self._language_manager.set_mode(new_language)
        self.accept()
