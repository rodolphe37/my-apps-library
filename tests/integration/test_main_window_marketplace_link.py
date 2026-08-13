"""Plugins menu should always offer a way to discover plugins on the
marketplace, even with the plugin system unavailable (plugin_manager=None) —
mirrors how "Manage Plugins…" is always present regardless of that."""

from PySide6.QtGui import QDesktopServices

from myapps.constants import MARKETPLACE_URL
from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.i18n import tr
from myapps.ui.main_window import MainWindow
from myapps.ui.theme.theme_manager import ThemeManager


def make_window(tmp_path, qtbot, qapp):
    pm = ProjectManager(path=tmp_path / "library.json")
    sm = SettingsManager(path=tmp_path / "settings.json")
    er = EditorRegistry(path=tmp_path / "editors.json")
    tm = ThemeManager(qapp)
    window = MainWindow(pm, sm, er, tm)
    qtbot.addWidget(window)
    return window


def test_plugins_menu_has_browse_marketplace_action(tmp_path, qtbot, qapp):
    window = make_window(tmp_path, qtbot, qapp)
    labels = [a.text() for a in window._plugins_menu.actions()]
    assert tr("menu.plugins.browseMarketplace") in labels


def test_browse_marketplace_action_opens_marketplace_url(tmp_path, qtbot, qapp, monkeypatch):
    window = make_window(tmp_path, qtbot, qapp)

    opened_urls = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened_urls.append(url.toString()))

    browse_action = next(
        a
        for a in window._plugins_menu.actions()
        if a.text() == tr("menu.plugins.browseMarketplace")
    )
    browse_action.trigger()

    assert opened_urls == [MARKETPLACE_URL]
