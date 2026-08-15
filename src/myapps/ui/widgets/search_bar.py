"""A simple debounced search box."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QLineEdit, QWidget

from myapps.i18n import tr


class SearchBar(QLineEdit):
    search_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self.retranslate()
        self.setClearButtonEnabled(True)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(lambda: self.search_changed.emit(self.text()))

        self.textChanged.connect(lambda _: self._debounce.start())

    def retranslate(self) -> None:
        """The placeholder is otherwise only set once in __init__ - unlike
        menus/dialogs, this widget is long-lived, so it needs to be told to
        refresh explicitly on language change (see MainWindow._on_language_changed)."""
        self.setPlaceholderText(tr("search.placeholder"))
