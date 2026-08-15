from PySide6.QtWidgets import QPushButton

from myapps.ui.dialogs.update_available_dialog import (
    UpdateAvailableDialog,
    upgrade_command_for_platform,
)


def test_upgrade_command_macos_mentions_brew_and_curl():
    command = upgrade_command_for_platform("Darwin")
    assert command is not None
    assert "brew upgrade --cask my-apps-library" in command
    assert "curl" in command


def test_upgrade_command_linux_is_curl_install_script():
    command = upgrade_command_for_platform("Linux")
    assert command is not None
    assert command.startswith("curl -fsSL")
    assert "packaging/linux/install.sh" in command


def test_upgrade_command_windows_is_none():
    # No winget command shown - README.md says the package isn't published
    # to the winget-pkgs community repo yet, so showing one would just fail
    # for whoever ran it. See the function's own docstring.
    assert upgrade_command_for_platform("Windows") is None


def test_dialog_constructs_without_raising(qtbot):
    dialog = UpdateAvailableDialog("0.6.0", "0.6.1")
    qtbot.addWidget(dialog)
    assert not dialog.skipped


def _find_button(dialog: UpdateAvailableDialog, text: str) -> QPushButton:
    return next(b for b in dialog.findChildren(QPushButton) if b.text() == text)


def test_dialog_skip_button_sets_skipped(qtbot):
    dialog = UpdateAvailableDialog("0.6.0", "0.6.1")
    qtbot.addWidget(dialog)

    _find_button(dialog, "Skip this version").click()

    assert dialog.skipped is True


def test_dialog_close_button_does_not_set_skipped(qtbot):
    dialog = UpdateAvailableDialog("0.6.0", "0.6.1")
    qtbot.addWidget(dialog)

    _find_button(dialog, "Close").click()

    assert dialog.skipped is False
