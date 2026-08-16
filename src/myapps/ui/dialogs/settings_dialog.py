"""Preferences dialog: theme mode/palette, language, and global default
editor."""

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
from myapps.ui.theme.theme_manager import ThemeManager


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings_manager: SettingsManager,
        editor_registry: EditorRegistry,
        parent: QWidget | None = None,
        language_manager: LanguageManager | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.settings.title"))
        self.setMinimumWidth(360)
        self._settings = settings_manager
        self._registry = editor_registry
        self._language_manager = language_manager
        self._theme_manager = theme_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setVerticalSpacing(10)
        layout.addLayout(form)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem(tr("dialog.settings.theme_system"), "system")
        self._theme_combo.addItem(tr("dialog.settings.theme_light"), "light")
        self._theme_combo.addItem(tr("dialog.settings.theme_dark"), "dark")
        current_theme = settings_manager.settings.theme_mode
        self._theme_combo.setCurrentIndex(max(0, self._theme_combo.findData(current_theme)))
        form.addRow(tr("dialog.settings.theme_label"), self._theme_combo)

        self._palette_combo = QComboBox()
        if theme_manager is not None:
            for palette_id, label in theme_manager.available_palette_choices():
                self._palette_combo.addItem(label, palette_id)
            current_palette = settings_manager.settings.theme_palette_id
            idx = self._palette_combo.findData(current_palette)
            self._palette_combo.setCurrentIndex(idx if idx >= 0 else 0)
        # Only worth showing once a plugin has actually contributed a
        # palette - otherwise it's a single-item "Default" dropdown with
        # nothing to choose between.
        if self._palette_combo.count() > 1:
            form.addRow(tr("dialog.settings.palette_label"), self._palette_combo)

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
        new_mode = self._theme_combo.currentData()
        new_palette = self._palette_combo.currentData() or "default"
        self._settings.set(
            theme_mode=new_mode,
            theme_palette_id=new_palette,
            language=new_language,
            global_default_editor_id=self._editor_combo.currentData(),
        )
        if self._language_manager is not None:
            self._language_manager.set_mode(new_language)
        if self._theme_manager is not None:
            self._theme_manager.set_palette(new_palette)
            self._theme_manager.set_mode(new_mode)
        self.accept()
