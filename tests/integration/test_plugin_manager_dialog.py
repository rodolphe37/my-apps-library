from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices

from myapps.constants import MARKETPLACE_URL
from myapps.core.project_manager import ProjectManager
from myapps.plugins.manager import PluginManager
from myapps.ui.dialogs.plugin_manager_dialog import PluginManagerDialog

REPO_ROOT = Path(__file__).resolve().parents[2]
OPEN_IN_TERMINAL_EXAMPLE = REPO_ROOT / "examples" / "plugins" / "open_in_terminal"


def test_dialog_opens_and_lists_installed_plugin(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)

    assert dialog._list.count() == 1
    item = dialog._list.item(0)
    assert "Open in Terminal" in item.text()
    assert item.checkState() == Qt.CheckState.Unchecked  # disabled by default


def test_checkbox_toggle_calls_enable_and_disable(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)

    # Auto-confirm the trust disclosure dialog that appears on enable.
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes)

    # Re-fetch the item after each toggle: enable()/disable() emit
    # plugins_changed, which the dialog reacts to by fully reloading its
    # QListWidget (clear() deletes the old item objects).
    dialog._list.item(0).setCheckState(Qt.CheckState.Checked)
    assert plugins._installed["open-in-terminal"].enabled is True

    dialog._list.item(0).setCheckState(Qt.CheckState.Unchecked)
    assert plugins._installed["open-in-terminal"].enabled is False


def test_browse_marketplace_opens_marketplace_url(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)

    opened_urls = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened_urls.append(url.toString()))

    dialog._browse_marketplace()

    assert opened_urls == [MARKETPLACE_URL]
