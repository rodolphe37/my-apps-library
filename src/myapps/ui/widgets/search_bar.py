"""A simple debounced search box."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QLineEdit, QWidget


class SearchBar(QLineEdit):
    search_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self.setPlaceholderText("Search projects…")
        self.setClearButtonEnabled(True)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(lambda: self.search_changed.emit(self.text()))

        self.textChanged.connect(lambda _: self._debounce.start())
