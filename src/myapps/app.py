"""QApplication bootstrap."""

from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from myapps.constants import APP_NAME, ORG_NAME
from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.i18n import LanguageManager
from myapps.plugins.manager import PluginManager
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
    theme_manager.set_mode(settings_manager.settings.theme_mode)

    plugin_manager = PluginManager(project_manager)
    plugin_manager.load_all_enabled()

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

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
