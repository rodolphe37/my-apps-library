"""Dialog-button helpers that relabel Qt's own built-in button text through
the app's own tr() catalog.

Both QDialogButtonBox's standard buttons (OK/Cancel/Close) and
QMessageBox.question()'s default Yes/No come from Qt's own bundled
translations (qtbase_<locale>.qm), loaded via QTranslator - this app never
installs one (it has its own complete i18n system instead, see
i18n/translator.py), so those labels stay in English regardless of the
active language unless explicitly relabeled, as this module does.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDialogButtonBox, QMessageBox, QWidget

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
