"""Plugin Manager dialog: list installed plugins, enable/disable, install
from a local .zip/folder, view details/permissions, and uninstall.

Each installed plugin is a card (`_PluginCard`): its own logo image if
`plugin.toml` declares one and the file actually ships (`manifest.icon_path`
- see plugins/manifest.py), otherwise a generated fallback badge in the
app's own brand gradient (see ui/theme/shapes.py, shared with the folder
icon painted in list/grid view). Enable/disable is a `ToggleSwitch`
(ui/widgets/toggle_switch.py), not a checkbox - selecting a card for
Details…/Remove is a separate action (a click anywhere on the card besides
the switch itself), a QListWidget + setItemWidget() is still what tracks
"which plugin is selected" underneath.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPainter, QPainterPath, QPalette, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from myapps.constants import MARKETPLACE_URL
from myapps.core.events import event_bus
from myapps.i18n import tr
from myapps.plugins.manager import (
    LoadedPlugin,
    PluginInstallError,
    PluginLoadState,
    PluginManager,
)
from myapps.plugins.manifest import PluginManifest
from myapps.plugins.sandbox import describe_permissions, trust_disclosure_text
from myapps.ui.theme.shapes import badge_pixmap
from myapps.ui.widgets.dialog_buttons import ask_yes_no, standard_button_box
from myapps.ui.widgets.toggle_switch import ToggleSwitch

_CARD_ICON_SIZE = 40
_DETAILS_ICON_SIZE = 48
_FALLBACK_GLYPH = "🧩"

_STATUS_KEYS = {
    PluginLoadState.LOADED: "dialog.plugins.status.loaded",
    PluginLoadState.DISABLED: "dialog.plugins.status.disabled",
    PluginLoadState.FAILED: "dialog.plugins.status.failed",
    PluginLoadState.DISCOVERED: "dialog.plugins.status.discovered",
}


def _style_muted(label: QLabel) -> None:
    """Dims a label to the palette's placeholder-text shade - theme-aware
    (light/dark, any plugin-contributed palette) without hardcoding a
    color or relying on a QSS `palette()` string (whose supported role-name
    spelling isn't consistent across Qt versions)."""
    palette = label.palette()
    muted = palette.color(QPalette.ColorRole.PlaceholderText)
    palette.setColor(QPalette.ColorRole.WindowText, muted)
    label.setPalette(palette)


def _plugin_icon_pixmap(manifest: PluginManifest, size: int) -> QPixmap:
    icon_path = manifest.icon_path
    if icon_path is not None:
        source = QPixmap(str(icon_path))
        if not source.isNull():
            return _rounded_square(source, size)
    return badge_pixmap(size, glyph=_FALLBACK_GLYPH)


def _rounded_square(source: QPixmap, size: int) -> QPixmap:
    """Center-crops `source` to a square then clips it to the same rounded
    corners the generated badge/folder icons use, so a plugin's own logo
    sits visually consistently alongside them."""
    scaled = source.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), size * 0.22, size * 0.22)
    painter.setClipPath(path)
    x = (scaled.width() - size) // 2
    y = (scaled.height() - size) // 2
    painter.drawPixmap(-x, -y, scaled)
    painter.end()
    return result


def _add_grid_row(grid: QGridLayout, row: int, label_text: str, value_text: str) -> int:
    label = QLabel(label_text)
    _style_muted(label)
    grid.addWidget(label, row, 0)
    value = QLabel(value_text)
    value.setWordWrap(True)
    grid.addWidget(value, row, 1)
    return row + 1


class _PluginCard(QFrame):
    """One installed plugin's row: logo/fallback icon, name + version +
    status, its short description, and a ToggleSwitch - everything but the
    switch is a `clicked` trigger for row selection (see the dialog's
    `_reload()`, which wires that to `QListWidget.setCurrentItem()`)."""

    clicked = Signal()

    def __init__(self, loaded: LoadedPlugin, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PluginCard")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)  # so QSS ':hover' actually fires
        self.plugin_id = loaded.manifest.id

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(_CARD_ICON_SIZE, _CARD_ICON_SIZE)
        icon_label.setPixmap(_plugin_icon_pixmap(loaded.manifest, _CARD_ICON_SIZE))
        row.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        name_label = QLabel(f"<b>{loaded.manifest.name}</b>")
        name_row.addWidget(name_label)
        version_label = QLabel(f"v{loaded.manifest.version}")
        _style_muted(version_label)
        name_row.addWidget(version_label)
        name_row.addStretch(1)
        text_col.addLayout(name_row)

        status_label = QLabel(tr(_STATUS_KEYS[loaded.state]))
        if loaded.state == PluginLoadState.FAILED:
            status_label.setStyleSheet("color: #d64545;")
        else:
            _style_muted(status_label)
        text_col.addWidget(status_label)

        if loaded.manifest.description:
            desc_label = QLabel(loaded.manifest.description)
            desc_label.setWordWrap(True)
            _style_muted(desc_label)
            text_col.addWidget(desc_label)

        row.addLayout(text_col, 1)

        self.switch = ToggleSwitch()
        # set_checked_silently(), not setChecked() - a freshly-built card
        # should appear already resting in the right position, not
        # visibly animate into it the instant the dialog opens (see the
        # widget's own docstring).
        self.switch.set_checked_silently(loaded.state == PluginLoadState.LOADED)
        row.addWidget(self.switch, 0, Qt.AlignmentFlag.AlignVCenter)

        if loaded.state == PluginLoadState.FAILED:
            self.setToolTip(tr("dialog.plugins.failed_tooltip", error=loaded.error))

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        """Toggles the QSS `[selected="true"]` attribute selector (see
        theme/styles/*.qss's `QFrame#PluginCard[selected="true"]` rule) -
        setItemWidget() means this card fully covers its QListWidgetItem's
        cell, so Qt's own native item-selected highlight never shows
        through; this is what actually indicates "this is the plugin
        Details…/Remove will act on" instead."""
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class PluginManagerDialog(QDialog):
    def __init__(self, plugin_manager: PluginManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.plugins.title"))
        self.setMinimumSize(520, 460)
        self.resize(600, 560)
        self._plugins = plugin_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        subtitle = QLabel(tr("dialog.plugins.subtitle"))
        subtitle.setWordWrap(True)
        _style_muted(subtitle)
        layout.addWidget(subtitle)

        self._list = QListWidget()
        self._list.setObjectName("PluginList")
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setSpacing(6)
        layout.addWidget(self._list, 1)
        self._reload()

        # A 2-column grid, not a 3-wide row: some localized labels are long
        # (French "Installer depuis un dossier…") and even a single row
        # split 3/2 still clipped them at a reasonable dialog width - a
        # fixed 2-column grid stays readable at any dialog width the user
        # resizes down to, not just the default. Also meaningful as a
        # split: "get more plugins" actions here, actions on the
        # *selected* plugin in their own row below.
        install_grid = QGridLayout()
        install_grid.setSpacing(8)
        browse_marketplace_btn = QPushButton(tr("dialog.plugins.browse_marketplace"))
        install_zip_btn = QPushButton(tr("dialog.plugins.install_zip"))
        install_folder_btn = QPushButton(tr("dialog.plugins.install_folder"))
        browse_marketplace_btn.clicked.connect(self._browse_marketplace)
        install_zip_btn.clicked.connect(self._install_zip)
        install_folder_btn.clicked.connect(self._install_folder)
        install_grid.addWidget(browse_marketplace_btn, 0, 0)
        install_grid.addWidget(install_zip_btn, 0, 1)
        install_grid.addWidget(install_folder_btn, 1, 0)
        layout.addLayout(install_grid)

        selection_row = QHBoxLayout()
        selection_row.setSpacing(8)
        details_btn = QPushButton(tr("dialog.plugins.details"))
        remove_btn = QPushButton(tr("dialog.plugins.remove"))
        details_btn.clicked.connect(self._show_details)
        remove_btn.clicked.connect(self._remove_selected)
        for b in (details_btn, remove_btn):
            selection_row.addWidget(b)
        selection_row.addStretch(1)
        layout.addLayout(selection_row)

        buttons = standard_button_box(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        event_bus.plugins_changed.connect(self._reload)
        self._list.currentItemChanged.connect(self._on_current_item_changed)

    # -- list population -------------------------------------------------

    def _reload(self, *_args) -> None:
        self._list.clear()
        for loaded in self._plugins.installed_plugins():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, loaded.manifest.id)
            card = _PluginCard(loaded)
            card.switch.toggled.connect(
                lambda checked, pid=loaded.manifest.id, sw=card.switch: self._on_toggle(
                    pid, checked, sw
                )
            )
            card.clicked.connect(lambda it=item: self._list.setCurrentItem(it))
            self._list.addItem(item)
            item.setSizeHint(card.sizeHint())
            self._list.setItemWidget(item, card)

    def _on_current_item_changed(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        if previous is not None:
            old_card = self._list.itemWidget(previous)
            if old_card is not None:
                old_card.set_selected(False)
        if current is not None:
            new_card = self._list.itemWidget(current)
            if new_card is not None:
                new_card.set_selected(True)

    def _selected_plugin_id(self) -> str | None:
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _selected_loaded_plugin(self) -> LoadedPlugin | None:
        plugin_id = self._selected_plugin_id()
        if not plugin_id:
            return None
        for loaded in self._plugins.installed_plugins():
            if loaded.manifest.id == plugin_id:
                return loaded
        return None

    # -- actions -------------------------------------------------------

    def _on_toggle(self, plugin_id: str, checked: bool, switch: ToggleSwitch) -> None:
        if checked:
            confirmed = ask_yes_no(
                self,
                tr("dialog.plugins.enable_title"),
                trust_disclosure_text() + tr("dialog.plugins.enable_confirm_suffix"),
            )
            if not confirmed:
                switch.blockSignals(True)
                switch.setChecked(False)
                switch.blockSignals(False)
                return
            self._plugins.enable(plugin_id)
        else:
            self._plugins.disable(plugin_id)

    def _browse_marketplace(self) -> None:
        QDesktopServices.openUrl(QUrl(MARKETPLACE_URL))

    def _install_zip(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("dialog.plugins.install_zip_title"),
            filter=tr("dialog.plugins.install_zip_filter"),
        )
        if path:
            self._try_install(path)

    def _install_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr("dialog.plugins.install_folder_title"))
        if path:
            self._try_install(path)

    def _try_install(self, path: str) -> None:
        try:
            self._plugins.install_from_path(path)
        except PluginInstallError as exc:
            QMessageBox.warning(self, tr("dialog.plugins.install_error_title"), str(exc))

    def _show_details(self) -> None:
        loaded = self._selected_loaded_plugin()
        if not loaded:
            return
        manifest = loaded.manifest

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("dialog.plugins.details_title"))
        dialog.setMinimumWidth(380)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(12)
        icon_label = QLabel()
        icon_label.setFixedSize(_DETAILS_ICON_SIZE, _DETAILS_ICON_SIZE)
        icon_label.setPixmap(_plugin_icon_pixmap(manifest, _DETAILS_ICON_SIZE))
        header.addWidget(icon_label)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(QLabel(f"<b>{manifest.name}</b>"))
        id_line = QLabel(f"v{manifest.version} · {manifest.id}")
        _style_muted(id_line)
        title_col.addWidget(id_line)
        header.addLayout(title_col, 1)
        layout.addLayout(header)

        if manifest.description:
            description = QLabel(manifest.description)
            description.setWordWrap(True)
            layout.addWidget(description)

        info_grid = QGridLayout()
        info_grid.setColumnStretch(1, 1)
        info_grid.setVerticalSpacing(4)
        row = _add_grid_row(
            info_grid,
            0,
            tr("dialog.plugins.details_author"),
            manifest.author or tr("dialog.plugins.unknown_author"),
        )
        _add_grid_row(
            info_grid,
            row,
            tr("dialog.plugins.details_license"),
            manifest.license or tr("dialog.plugins.unspecified_license"),
        )
        layout.addLayout(info_grid)

        permissions_title = QLabel(f"<b>{tr('dialog.plugins.details_permissions')}</b>")
        layout.addWidget(permissions_title)
        for permission in describe_permissions(manifest) or [tr("dialog.plugins.no_permissions")]:
            permission_label = QLabel(f"• {permission}")
            permission_label.setWordWrap(True)
            layout.addWidget(permission_label)

        buttons = standard_button_box(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def _remove_selected(self) -> None:
        plugin_id = self._selected_plugin_id()
        if not plugin_id:
            return
        confirmed = ask_yes_no(
            self,
            tr("dialog.plugins.remove_confirm_title"),
            tr("dialog.plugins.remove_confirm_body", id=plugin_id),
        )
        if confirmed:
            self._plugins.uninstall(plugin_id)
