"""QApplication bootstrap."""

from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from myapps.constants import APP_NAME, ORG_NAME, VERSION
from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.core.update_checker import UpdateChecker
from myapps.editors.registry import EditorRegistry
from myapps.i18n import LanguageManager
from myapps.plugins.manager import PluginManager
from myapps.ui.dialogs.update_available_dialog import UpdateAvailableDialog
from myapps.ui.main_window import MainWindow
from myapps.ui.resources import app_icon_path
from myapps.ui.theme.theme_manager import ThemeManager
from myapps.utils.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> int:
    configure_logging()
    logger.info("Starting %s", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(True)
    app.setWindowIcon(QIcon(str(app_icon_path())))

    project_manager = ProjectManager()
    settings_manager = SettingsManager()
    editor_registry = EditorRegistry()
    if not editor_registry.list_editors():
        # First run (or empty cache): detect editors up front so "Open" works
        # immediately instead of the user having to know to hit Refresh.
        editor_registry.refresh()

    theme_manager = ThemeManager(app)

    plugin_manager = PluginManager(project_manager)
    plugin_manager.load_all_enabled()

    # Palettes/mode applied only after plugins are loaded, so a
    # plugin-contributed palette picked in a previous session is available
    # from the very first paint rather than flashing the default first.
    theme_manager.set_available_palettes(plugin_manager.collect_theme_palettes())
    theme_manager.set_palette(settings_manager.settings.theme_palette_id)
    theme_manager.set_mode(settings_manager.settings.theme_mode)

    language_manager = LanguageManager()
    language_manager.set_plugin_translations(plugin_manager.collect_translations())
    language_manager.set_mode(settings_manager.settings.language)

    window = MainWindow(
        project_manager,
        settings_manager,
        editor_registry,
        theme_manager,
        plugin_manager,
        language_manager,
    )
    window.show()

    # Parented to the window so it's kept alive for the async reply's
    # lifetime without needing a `main()`-local variable for that purpose;
    # fired after show() so a slow/offline network check never delays the
    # window a user is actively waiting to see.
    update_checker = UpdateChecker(window)
    update_checker.update_available.connect(
        lambda latest: _on_update_available(latest, settings_manager, window)
    )
    update_checker.check(VERSION)

    return app.exec()


def _on_update_available(
    latest_version: str, settings_manager: SettingsManager, window: MainWindow
) -> None:
    if settings_manager.settings.dismissed_update_version == latest_version:
        return  # user already clicked "Skip this version" for this exact one
    dialog = UpdateAvailableDialog(VERSION, latest_version, window)
    dialog.exec()
    if dialog.skipped:
        settings_manager.set(dismissed_update_version=latest_version)


if __name__ == "__main__":
    sys.exit(main())
