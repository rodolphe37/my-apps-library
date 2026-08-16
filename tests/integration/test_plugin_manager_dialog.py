from pathlib import Path

from PySide6.QtGui import QDesktopServices

from myapps.constants import MARKETPLACE_URL
from myapps.core.project_manager import ProjectManager
from myapps.plugins.manager import PluginManager
from myapps.ui.dialogs.plugin_manager_dialog import PluginManagerDialog, _PluginCard

REPO_ROOT = Path(__file__).resolve().parents[2]
OPEN_IN_TERMINAL_EXAMPLE = REPO_ROOT / "examples" / "plugins" / "open_in_terminal"


def _card(dialog: PluginManagerDialog, row: int) -> _PluginCard:
    item = dialog._list.item(row)
    return dialog._list.itemWidget(item)


def test_dialog_opens_and_lists_installed_plugin(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)

    assert dialog._list.count() == 1
    card = _card(dialog, 0)
    assert card.plugin_id == "open-in-terminal"
    assert card.switch.isChecked() is False  # disabled by default

    from PySide6.QtWidgets import QLabel

    assert any("Open in Terminal" in lbl.text() for lbl in card.findChildren(QLabel))


def test_toggle_switch_calls_enable_and_disable(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)

    # Auto-confirm the trust disclosure dialog that appears on enable.
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes)

    # Re-fetch the card after each toggle: enable()/disable() emit
    # plugins_changed, which the dialog reacts to by fully reloading its
    # QListWidget (clear() deletes the old item/card objects).
    _card(dialog, 0).switch.setChecked(True)
    assert plugins._installed["open-in-terminal"].enabled is True

    _card(dialog, 0).switch.setChecked(False)
    assert plugins._installed["open-in-terminal"].enabled is False


def test_declining_enable_confirmation_reverts_switch(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)

    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.No)

    card = _card(dialog, 0)
    card.switch.setChecked(True)

    assert plugins._installed["open-in-terminal"].enabled is False
    assert card.switch.isChecked() is False  # reverted, no plugins_changed/reload happened


def test_browse_marketplace_opens_marketplace_url(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)

    opened_urls = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened_urls.append(url.toString()))

    dialog._browse_marketplace()

    assert opened_urls == [MARKETPLACE_URL]
