import zipfile
from pathlib import Path

from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from myapps.constants import MARKETPLACE_URL
from myapps.core.project_manager import ProjectManager
from myapps.plugins.manager import PluginManager
from myapps.ui.dialogs.plugin_manager_dialog import PluginManagerDialog, _PluginCard

REPO_ROOT = Path(__file__).resolve().parents[2]
OPEN_IN_TERMINAL_EXAMPLE = REPO_ROOT / "examples" / "plugins" / "open_in_terminal"


def _make_update_zip(tmp_path: Path, version: str = "0.2.0") -> Path:
    """A newer version of the open-in-terminal example: same id, bumped
    version - what PluginMarketplaceClient.download_finished would have
    handed to _on_download_finished after a real download. Written into
    its own subfolder, not tmp_path directly - _on_download_finished
    rmtree's the zip's parent dir once it's done with it (matching what
    the real download-to-temp-dir flow does), which would otherwise wipe
    out this whole test's fixture directory."""
    download_dir = tmp_path / "update-download"
    download_dir.mkdir(exist_ok=True)
    zip_path = download_dir / f"open-in-terminal-{version}.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(
            "plugin.toml",
            f"""[plugin]
id = "open-in-terminal"
name = "Open in Terminal"
version = "{version}"
entry_point = "plugin:OpenInTerminalPlugin"
""",
        )
        zf.writestr(
            "plugin.py",
            "from myapps.plugins.api import PluginBase\n\n"
            "class OpenInTerminalPlugin(PluginBase):\n    pass\n",
        )
    return zip_path


def _card(dialog: PluginManagerDialog, row: int) -> _PluginCard:
    item = dialog._list.item(row)
    return dialog._list.itemWidget(item)


_LONG_DESCRIPTION = (
    "This description is deliberately long enough that it must wrap onto "
    "several lines inside a normal-sized dialog, instead of fitting on one - "
    "exercising the exact case that used to make every card's text spill "
    "past the list's right edge instead of wrapping into a taller row."
)


def _install_plugin_with_long_description(
    tmp_path: Path, plugins: PluginManager, plugin_id: str = "verbose-plugin"
) -> None:
    source = tmp_path / f"{plugin_id}-source"
    source.mkdir()
    (source / "plugin.toml").write_text(
        f"""[plugin]
id = "{plugin_id}"
name = "Verbose Plugin"
version = "1.0.0"
entry_point = "plugin:VerbosePlugin"
description = "{_LONG_DESCRIPTION}"
""",
        encoding="utf-8",
    )
    (source / "plugin.py").write_text(
        "from myapps.plugins.api import PluginBase\n\nclass VerbosePlugin(PluginBase):\n    pass\n",
        encoding="utf-8",
    )
    plugins.install_from_path(source)


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
    monkeypatch.setattr(
        "myapps.ui.dialogs.plugin_manager_dialog.ask_yes_no", lambda *a, **kw: True
    )

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

    monkeypatch.setattr(
        "myapps.ui.dialogs.plugin_manager_dialog.ask_yes_no", lambda *a, **kw: False
    )

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


def test_update_available_shows_badge_and_button(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog.show()  # isVisible() below needs the whole ancestor chain shown

    card = _card(dialog, 0)
    assert card._update_row.isVisible() is False

    dialog._on_update_available("open-in-terminal", "0.2.0")

    assert card._update_row.isVisible() is True
    assert "0.2.0" in card._update_label.text()
    assert card._update_button.isEnabled() is True


def test_clicking_update_button_disables_it_while_downloading(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog._on_update_available("open-in-terminal", "0.2.0")

    card = _card(dialog, 0)
    card._update_button.click()

    assert card._update_button.isEnabled() is False


def test_successful_update_bumps_version_and_clears_badge(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog.show()  # isVisible() below needs the whole ancestor chain shown
    dialog._on_update_available("open-in-terminal", "0.2.0")

    zip_path = _make_update_zip(tmp_path)
    # What PluginMarketplaceClient.download_finished would emit after a
    # real download - simulated directly, see conftest.py's docstring.
    dialog._on_download_finished("open-in-terminal", str(zip_path))

    assert plugins._installed["open-in-terminal"].version == "0.2.0"
    # update_from_path()'s plugins_changed emit already triggered a
    # _reload() - re-fetch, the old card object is gone.
    assert _card(dialog, 0)._update_row.isVisible() is False


def test_failed_download_shows_warning_and_resets_button(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog._on_update_available("open-in-terminal", "0.2.0")
    card = _card(dialog, 0)
    card.set_updating()

    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *a, **kw: warnings.append(a) or QMessageBox.StandardButton.Ok
    )

    dialog._on_download_failed("open-in-terminal", "network went away")

    assert len(warnings) == 1
    assert card._update_button.isEnabled() is True
    # Still installed at the old version - a failed download never touched it.
    assert plugins._installed["open-in-terminal"].version == "0.1.0"


def test_card_width_never_exceeds_viewport_even_with_long_description(tmp_path, qtbot):
    """Regression test: a long word-wrapped description used to leave a
    card's setItemWidget() sizeHint frozen at whatever (too-wide) size it
    happened to compute before the dialog had settled into its real
    on-screen width - clipping every card's text at the list's actual
    (narrower) viewport edge instead of wrapping it into a taller row."""
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    _install_plugin_with_long_description(tmp_path, plugins)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog.resize(600, 560)
    dialog.show()
    qtbot.wait(50)

    card = _card(dialog, 0)
    viewport_width = dialog._list.viewport().width()
    item = dialog._list.item(0)

    # The card's own right edge - not just its width - is what must stay
    # inside the viewport: QListWidget insets every item by setSpacing()'s
    # value from the viewport's left edge too, so a card exactly as wide as
    # the viewport is actually a few pixels too wide once positioned.
    assert card.geometry().right() <= viewport_width - 1
    assert item.sizeHint().width() <= viewport_width
    # A long description wrapped across several lines needs real height -
    # taller than a single name+status+one-line-description row would be.
    assert item.sizeHint().height() > 90


def test_resizing_dialog_resyncs_card_width(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog.resize(600, 560)
    dialog.show()
    qtbot.wait(50)

    dialog.resize(420, 560)
    qtbot.wait(50)

    card = _card(dialog, 0)
    assert card.geometry().right() <= dialog._list.viewport().width() - 1


def test_cards_fill_width_without_a_gap_when_nothing_needs_to_scroll(tmp_path, qtbot):
    """A too-cautious fix for the clipping bug above (always reserving the
    vertical scrollbar's width, whether or not one is actually needed)
    traded clipped cards for a permanent, pointless empty strip on the
    right of every card - just as wrong, in the opposite direction."""
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog.resize(600, 560)
    dialog.show()
    qtbot.wait(50)

    assert dialog._list.verticalScrollBar().isVisible() is False
    card = _card(dialog, 0)
    viewport_width = dialog._list.viewport().width()
    # Allowed to be a couple of px narrower than the viewport (the item's
    # own left inset, see _sync_card_widths()'s docstring) but not reserve
    # a whole scrollbar's worth of unused space on top of that.
    assert card.geometry().right() >= viewport_width - dialog._list.spacing() - 2


def test_cards_fit_next_to_scrollbar_when_content_needs_to_scroll(tmp_path, qtbot):
    """The mirror image of the test above: once there IS enough content to
    need scrolling, cards must actually make room for the scrollbar rather
    than running underneath it."""
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins = PluginManager(pm, plugins_dir=tmp_path / "plugins")
    plugins.install_from_path(OPEN_IN_TERMINAL_EXAMPLE)
    for i in range(6):
        _install_plugin_with_long_description(tmp_path, plugins, plugin_id=f"extra-{i}")

    dialog = PluginManagerDialog(plugins, None)
    qtbot.addWidget(dialog)
    dialog.resize(600, 560)
    dialog.show()
    qtbot.wait(50)

    assert dialog._list.verticalScrollBar().isVisible() is True
    viewport_width = dialog._list.viewport().width()
    for i in range(dialog._list.count()):
        card = _card(dialog, i)
        assert card.geometry().right() <= viewport_width - 1
