"""Grid-of-glyphs icon picker, shared by categories and projects. Shows the
built-in pack plus any icon pack contributed by an enabled plugin (see
plugins/api.py's IconPack/IconDef), each as its own labeled section."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from myapps.i18n import tr
from myapps.plugins.api import IconPack
from myapps.ui.theme.builtin_icons import BUILTIN_ICON_PACK
from myapps.ui.widgets.dialog_buttons import standard_button_box

_COLUMNS = 8


class IconPickerDialog(QDialog):
    def __init__(
        self,
        plugin_packs: list[IconPack],
        current: str | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.icon_picker.title"))
        self.setMinimumSize(420, 480)
        self._selected: str | None = current

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 16)
        outer.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        for pack in [BUILTIN_ICON_PACK, *plugin_packs]:
            content_layout.addWidget(self._section_label(pack.label))
            content_layout.addWidget(self._grid_for(pack))

        content_layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        clear_btn = QPushButton(tr("dialog.icon_picker.clear"))
        clear_btn.clicked.connect(self._clear)
        outer.addWidget(clear_btn)

        buttons = standard_button_box(
            QDialogButtonBox.StandardButton.Ok, QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 600; margin-top: 8px;")
        return label

    def _grid_for(self, pack: IconPack) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(4)
        for index, icon_def in enumerate(pack.icons):
            btn = QPushButton(icon_def.glyph)
            btn.setToolTip(icon_def.label)
            btn.setFixedSize(40, 40)
            btn.setCheckable(True)
            btn.setChecked(icon_def.glyph == self._selected)
            btn.clicked.connect(lambda _checked, g=icon_def.glyph: self._select(g))
            grid.addWidget(btn, index // _COLUMNS, index % _COLUMNS)
        return container

    def _select(self, glyph: str) -> None:
        self._selected = glyph
        # Uncheck every other button across every section so exactly one
        # stays highlighted, regardless of which pack it came from.
        for btn in self.findChildren(QPushButton):
            if btn.text() != glyph:
                btn.setChecked(False)

    def _clear(self) -> None:
        self._selected = None
        for btn in self.findChildren(QPushButton):
            btn.setChecked(False)

    def selected_icon(self) -> str | None:
        return self._selected
