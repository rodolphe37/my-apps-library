"""Plugin Manager dialog: list installed plugins, enable/disable, install
from a local .zip/folder, view details/permissions, and uninstall. Follows
`category_manager_dialog.py`'s established shape.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
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
from myapps.plugins.sandbox import describe_permissions, trust_disclosure_text


class PluginManagerDialog(QDialog):
    def __init__(self, plugin_manager: PluginManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.plugins.title"))
        self.setMinimumSize(460, 420)
        self._plugins = plugin_manager

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        self._list.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._list)
        self._reload()

        btn_row = QHBoxLayout()
        browse_marketplace_btn = QPushButton(tr("dialog.plugins.browse_marketplace"))
        install_zip_btn = QPushButton(tr("dialog.plugins.install_zip"))
        install_folder_btn = QPushButton(tr("dialog.plugins.install_folder"))
        details_btn = QPushButton(tr("dialog.plugins.details"))
        remove_btn = QPushButton(tr("dialog.plugins.remove"))
        browse_marketplace_btn.clicked.connect(self._browse_marketplace)
        install_zip_btn.clicked.connect(self._install_zip)
        install_folder_btn.clicked.connect(self._install_folder)
        details_btn.clicked.connect(self._show_details)
        remove_btn.clicked.connect(self._remove_selected)
        for b in (
            browse_marketplace_btn,
            install_zip_btn,
            install_folder_btn,
            details_btn,
            remove_btn,
        ):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        event_bus.plugins_changed.connect(self._reload)

    # -- list population -------------------------------------------------

    def _reload(self, *_args) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        for loaded in self._plugins.installed_plugins():
            item = QListWidgetItem(self._row_text(loaded))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if loaded.state == PluginLoadState.LOADED
                else Qt.CheckState.Unchecked
            )
            item.setData(Qt.ItemDataRole.UserRole, loaded.manifest.id)
            if loaded.state == PluginLoadState.FAILED:
                item.setToolTip(tr("dialog.plugins.failed_tooltip", error=loaded.error))
            self._list.addItem(item)
        self._list.blockSignals(False)

    @staticmethod
    def _row_text(loaded: LoadedPlugin) -> str:
        status_key = {
            PluginLoadState.LOADED: "dialog.plugins.status.loaded",
            PluginLoadState.DISABLED: "dialog.plugins.status.disabled",
            PluginLoadState.FAILED: "dialog.plugins.status.failed",
            PluginLoadState.DISCOVERED: "dialog.plugins.status.discovered",
        }[loaded.state]
        return tr(
            "dialog.plugins.row_format",
            name=loaded.manifest.name,
            version=loaded.manifest.version,
            status=tr(status_key),
        )

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

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        plugin_id = item.data(Qt.ItemDataRole.UserRole)
        wants_enabled = item.checkState() == Qt.CheckState.Checked
        if wants_enabled:
            confirm = QMessageBox.question(
                self,
                tr("dialog.plugins.enable_title"),
                trust_disclosure_text() + tr("dialog.plugins.enable_confirm_suffix"),
            )
            if confirm != QMessageBox.StandardButton.Yes:
                self._list.blockSignals(True)
                item.setCheckState(Qt.CheckState.Unchecked)
                self._list.blockSignals(False)
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
        permissions = describe_permissions(manifest) or [tr("dialog.plugins.no_permissions")]
        text = tr(
            "dialog.plugins.details_body",
            name=manifest.name,
            version=manifest.version,
            id=manifest.id,
            author=manifest.author or tr("dialog.plugins.unknown_author"),
            license=manifest.license or tr("dialog.plugins.unspecified_license"),
            description=manifest.description,
            permissions="\n- ".join(permissions),
        )
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("dialog.plugins.details_title"))
        layout = QVBoxLayout(dialog)
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def _remove_selected(self) -> None:
        plugin_id = self._selected_plugin_id()
        if not plugin_id:
            return
        confirm = QMessageBox.question(
            self,
            tr("dialog.plugins.remove_confirm_title"),
            tr("dialog.plugins.remove_confirm_body", id=plugin_id),
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._plugins.uninstall(plugin_id)
