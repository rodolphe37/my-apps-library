"""Dialog helpers that relabel Qt's own built-in button text through the
app's own tr() catalog, and a styled replacement for QInputDialog.getText().

QDialogButtonBox's standard buttons (OK/Cancel/Close), QMessageBox.question()'s
default Yes/No, and QInputDialog's own OK/Cancel all come from Qt's own
bundled translations (qtbase_<locale>.qm), loaded via QTranslator - this app
never installs one (it has its own complete i18n system instead, see
i18n/translator.py), so those labels stay in English regardless of the
active language unless explicitly relabeled/rebuilt, as this module does.
QInputDialog's own bare, unstyled layout (a label butted directly against
the field, default OS margins) also doesn't match the rest of the app's
dialogs, which prompt_text() fixes at the same time.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from myapps.i18n import tr

_LABEL_KEYS: dict[QDialogButtonBox.StandardButton, str] = {
    QDialogButtonBox.StandardButton.Ok: "action.ok",
    QDialogButtonBox.StandardButton.Cancel: "action.cancel",
    QDialogButtonBox.StandardButton.Close: "action.close",
}


def standard_button_box(*standard_buttons: QDialogButtonBox.StandardButton) -> QDialogButtonBox:
    """Equivalent to `QDialogButtonBox(a | b | ...)`, except every standard
    button's displayed text is replaced by this app's own translation.
    Native per-platform button ordering/icons are untouched - only the
    label changes, via `QAbstractButton.setText()` on the button
    `QDialogButtonBox` already created for that role."""
    combined = QDialogButtonBox.StandardButton.NoButton
    for standard_button in standard_buttons:
        combined |= standard_button
    box = QDialogButtonBox(combined)
    for standard_button, key in _LABEL_KEYS.items():
        button = box.button(standard_button)
        if button is not None:
            button.setText(tr(key))
    return box


def ask_yes_no(parent: QWidget | None, title: str, text: str) -> bool:
    """Equivalent to `QMessageBox.question(parent, title, text) ==
    QMessageBox.StandardButton.Yes`, except the two buttons show this
    app's own Yes/No translation instead of Qt's untranslated default -
    see this module's docstring. Returns True for Yes, False for No or the
    box being dismissed any other way (closed, Escape, ...)."""
    box = QMessageBox(QMessageBox.Icon.Question, title, text, parent=parent)
    yes_button = box.addButton(tr("action.yes"), QMessageBox.ButtonRole.YesRole)
    box.addButton(tr("action.no"), QMessageBox.ButtonRole.NoRole)
    box.setDefaultButton(yes_button)
    box.exec()
    return box.clickedButton() is yes_button


def prompt_text(parent: QWidget | None, title: str, label: str, text: str = "") -> tuple[str, bool]:
    """Drop-in replacement for `QInputDialog.getText(parent, title, label,
    text=text)` - same (str, bool) return shape (the text, and whether OK
    was pressed) - with this app's own translated OK/Cancel and a proper
    label-above-field layout instead of QInputDialog's bare default one."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(340)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 16)
    layout.setSpacing(10)

    label_widget = QLabel(label)
    layout.addWidget(label_widget)

    line_edit = QLineEdit(text)
    line_edit.selectAll()
    line_edit.returnPressed.connect(dialog.accept)  # Enter submits, like QInputDialog
    layout.addWidget(line_edit)

    buttons = standard_button_box(
        QDialogButtonBox.StandardButton.Ok, QDialogButtonBox.StandardButton.Cancel
    )
    ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    ok_button.setDefault(True)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    line_edit.setFocus(Qt.FocusReason.PopupFocusReason)
    accepted = dialog.exec() == QDialog.DialogCode.Accepted
    return line_edit.text(), accepted
