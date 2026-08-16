"""UpdateAvailableDialog: shown when UpdateChecker (core/update_checker.py)
finds a GitHub release newer than this build. Gives the exact upgrade
command for the current OS, kept in sync by hand with README.md's own
Installation section - same tradeoff packaging/homebrew/bump_cask.py's
docstring already accepts elsewhere in this codebase: a handful of
well-commented literal strings, not worth templating from the README
itself for something this small and this rarely-changing.
"""

from __future__ import annotations

import platform

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from myapps.i18n import tr

RELEASES_URL = "https://github.com/rodolphe37/my-apps-library/releases/latest"
_INSTALL_SCRIPT_MACOS = (
    "https://raw.githubusercontent.com/rodolphe37/my-apps-library/main/packaging/macos/install.sh"
)
_INSTALL_SCRIPT_LINUX = (
    "https://raw.githubusercontent.com/rodolphe37/my-apps-library/main/packaging/linux/install.sh"
)


def upgrade_command_for_platform(system: str | None = None) -> str | None:
    """The real upgrade command for this OS, or None when there isn't a
    reliable one yet (Windows: winget upgrade would need the package
    published to the winget-pkgs community repo, which README.md's own
    Installation section already says hasn't happened - showing that
    command as if it worked would be actively misleading). `system`
    defaults to platform.system()'s own value, parameterized for tests."""
    system = system or platform.system()
    if system == "Darwin":
        return (
            "brew upgrade --cask my-apps-library\n"
            "# installed via the script instead? just re-run it:\n"
            f"curl -fsSL {_INSTALL_SCRIPT_MACOS} | bash"
        )
    if system == "Linux":
        return f"curl -fsSL {_INSTALL_SCRIPT_LINUX} | bash"
    return None  # Windows - no reliable one-liner yet, see docstring


class UpdateAvailableDialog(QDialog):
    def __init__(
        self, current_version: str, latest_version: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.update.title"))
        self.setMinimumWidth(460)
        self._skipped = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        header = QLabel(tr("dialog.update.header", latest=latest_version, current=current_version))
        header.setWordWrap(True)
        layout.addWidget(header)

        self._command_text = upgrade_command_for_platform()
        if self._command_text:
            layout.addWidget(QLabel(tr("dialog.update.command_label")))
            command_box = QTextEdit()
            command_box.setPlainText(self._command_text)
            command_box.setReadOnly(True)
            command_box.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            command_box.setFixedHeight(64 if "\n" in self._command_text else 36)
            layout.addWidget(command_box)

            copy_btn = QPushButton(tr("dialog.update.copy"))
            copy_btn.clicked.connect(self._copy_command)
            layout.addWidget(copy_btn)
        else:
            no_command_note = QLabel(tr("dialog.update.no_command_note"))
            no_command_note.setWordWrap(True)
            layout.addWidget(no_command_note)

        button_row = QHBoxLayout()
        view_release_btn = QPushButton(tr("dialog.update.view_release"))
        view_release_btn.clicked.connect(self._open_release_page)
        button_row.addWidget(view_release_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        buttons = QDialogButtonBox()
        skip_btn = buttons.addButton(
            tr("dialog.update.skip_version"), QDialogButtonBox.ButtonRole.DestructiveRole
        )
        close_btn = buttons.addButton(
            tr("dialog.update.close"), QDialogButtonBox.ButtonRole.RejectRole
        )
        skip_btn.clicked.connect(self._skip)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def skipped(self) -> bool:
        """True once the user has clicked "Skip this version" - the caller
        (app.py) checks this after exec() to decide whether to persist the
        dismissal, keeping this dialog itself free of any SettingsManager
        dependency."""
        return self._skipped

    def _skip(self) -> None:
        self._skipped = True
        self.reject()

    def _copy_command(self) -> None:
        if self._command_text:
            QGuiApplication.clipboard().setText(self._command_text)

    def _open_release_page(self) -> None:
        QDesktopServices.openUrl(QUrl(RELEASES_URL))
