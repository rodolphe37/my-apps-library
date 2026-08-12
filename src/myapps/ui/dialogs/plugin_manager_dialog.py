"""Plugin Manager dialog: list installed plugins, enable/disable, install
from a local .zip/folder, view details/permissions, and uninstall. Follows
`category_manager_dialog.py`'s established shape.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
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

from myapps.core.events import event_bus
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
        self.setWindowTitle("Manage Plugins")
        self.setMinimumSize(460, 420)
        self._plugins = plugin_manager

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        self._list.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._list)
        self._reload()

        btn_row = QHBoxLayout()
        install_zip_btn = QPushButton("Install from .zip…")
        install_folder_btn = QPushButton("Install from Folder…")
        details_btn = QPushButton("Details…")
        remove_btn = QPushButton("Remove")
        install_zip_btn.clicked.connect(self._install_zip)
        install_folder_btn.clicked.connect(self._install_folder)
        details_btn.clicked.connect(self._show_details)
        remove_btn.clicked.connect(self._remove_selected)
        for b in (install_zip_btn, install_folder_btn, details_btn, remove_btn):
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
                item.setToolTip(f"Failed to load: {loaded.error}")
            self._list.addItem(item)
        self._list.blockSignals(False)

    @staticmethod
    def _row_text(loaded: LoadedPlugin) -> str:
        status = {
            PluginLoadState.LOADED: "loaded",
            PluginLoadState.DISABLED: "disabled",
            PluginLoadState.FAILED: "failed",
            PluginLoadState.DISCOVERED: "discovered",
        }[loaded.state]
        return f"{loaded.manifest.name} ({loaded.manifest.version}) — {status}"

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
                "Enable Plugin",
                trust_disclosure_text() + "\n\nEnable this plugin?",
            )
            if confirm != QMessageBox.StandardButton.Yes:
                self._list.blockSignals(True)
                item.setCheckState(Qt.CheckState.Unchecked)
                self._list.blockSignals(False)
                return
            self._plugins.enable(plugin_id)
        else:
            self._plugins.disable(plugin_id)

    def _install_zip(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Plugin .zip", filter="Zip files (*.zip)"
        )
        if path:
            self._try_install(path)

    def _install_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Plugin Folder")
        if path:
            self._try_install(path)

    def _try_install(self, path: str) -> None:
        try:
            self._plugins.install_from_path(path)
        except PluginInstallError as exc:
            QMessageBox.warning(self, "Couldn't Install Plugin", str(exc))

    def _show_details(self) -> None:
        loaded = self._selected_loaded_plugin()
        if not loaded:
            return
        manifest = loaded.manifest
        permissions = describe_permissions(manifest) or ["(none declared)"]
        text = (
            f"{manifest.name}  v{manifest.version}\n"
            f"ID: {manifest.id}\n"
            f"Author: {manifest.author or '(unknown)'}\n"
            f"License: {manifest.license or '(unspecified)'}\n\n"
            f"{manifest.description}\n\n"
            f"Permissions:\n- " + "\n- ".join(permissions)
        )
        dialog = QDialog(self)
        dialog.setWindowTitle("Plugin Details")
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
            self, "Remove Plugin", f"Remove plugin {plugin_id!r}? This deletes its files."
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._plugins.uninstall(plugin_id)
