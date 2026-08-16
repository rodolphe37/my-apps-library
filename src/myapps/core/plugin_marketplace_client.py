"""Checks an installed plugin for a newer version on the marketplace, and
downloads it - both against the marketplace's public, no-auth API (the
same endpoints the CLI and web app already use: GET /api/plugins/{id} for
the current version, GET /api/plugins/{id}/download for the zip). Used by
PluginManagerDialog for the "Update available" badge/button on a card.

Same spirit as core/update_checker.py (the app's own update check): fully
async (QNetworkAccessManager), and silent on any failure (offline,
marketplace down, or - very commonly - a plugin that was never actually
published there at all) rather than surfacing an error for something that
was only ever a nice-to-have background check.

The marketplace's `slug` is architecturally decoupled from a plugin's own
`plugin.toml` [plugin].id (see the marketplace's Plugin model) - but every
plugin published so far has slug == plugin_manifest_id (that's what
`create_draft` sets it to, and there's no way to change a slug after the
fact yet), so using a plugin's own id as the slug in these requests works
for every plugin that exists today. If that ever changes, this is the
place to add a real id->slug lookup.
"""

from __future__ import annotations

import json
import logging
import tempfile
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from myapps.constants import MARKETPLACE_API_URL
from myapps.utils.version_utils import is_newer

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_MS = 8000
USER_AGENT = "MyAppsLibrary-PluginUpdateCheck"


def parse_latest_version(raw_response: bytes, current_version: str) -> str | None:
    """The pure half of the "check" response handling (see
    core/update_checker.py's parse_latest_version, same shape) - given the
    API's raw JSON body, returns the plugin's published `version` if it's
    newer than `current_version`, else None. Covers "malformed JSON",
    "missing version field", and "not actually newer" the same way, since
    none of them should ever surface to the user."""
    try:
        payload = json.loads(raw_response.decode("utf-8"))
        latest_version = payload["version"]
    except (ValueError, KeyError, UnicodeDecodeError) as exc:
        logger.info("Plugin update check failed (bad response): %s", exc)
        return None
    if not isinstance(latest_version, str) or not latest_version:
        return None
    return latest_version if is_newer(latest_version, current_version) else None


class PluginMarketplaceClient(QObject):
    # plugin_id, latest_version - only emitted when a real, newer version exists.
    update_available = Signal(str, str)
    # plugin_id, local path to the downloaded .zip (caller's responsibility
    # to delete once PluginManager.update_from_path() has consumed it).
    download_finished = Signal(str, str)
    # plugin_id, a short human-readable reason.
    download_failed = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Held as an attribute, not a local - see update_checker.py's own
        # UpdateChecker.__init__ for why (must outlive the async request).
        self._manager = QNetworkAccessManager(self)

    def check_for_update(self, plugin_id: str, current_version: str) -> None:
        reply = self._manager.get(self._request(f"/api/plugins/{plugin_id}"))
        reply.finished.connect(lambda: self._on_check_finished(reply, plugin_id, current_version))

    def _on_check_finished(
        self, reply: QNetworkReply, plugin_id: str, current_version: str
    ) -> None:
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            # Very often just "this plugin isn't on the marketplace" (404),
            # same non-event as offline/down - see module docstring.
            logger.info("Plugin update check for %r failed: %s", plugin_id, reply.errorString())
            return
        latest_version = parse_latest_version(bytes(reply.readAll()), current_version)
        if latest_version is not None:
            self.update_available.emit(plugin_id, latest_version)

    def download_update(self, plugin_id: str) -> None:
        reply = self._manager.get(self._request(f"/api/plugins/{plugin_id}/download"))
        reply.finished.connect(lambda: self._on_download_finished(reply, plugin_id))

    def _on_download_finished(self, reply: QNetworkReply, plugin_id: str) -> None:
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.download_failed.emit(plugin_id, reply.errorString())
            return
        data = bytes(reply.readAll())
        try:
            tmp_dir = Path(tempfile.mkdtemp(prefix="myapps-plugin-update-dl-"))
            zip_path = tmp_dir / f"{plugin_id}-{uuid.uuid4().hex}.zip"
            zip_path.write_bytes(data)
        except OSError as exc:
            self.download_failed.emit(plugin_id, str(exc))
            return
        self.download_finished.emit(plugin_id, str(zip_path))

    @staticmethod
    def _request(path: str) -> QNetworkRequest:
        request = QNetworkRequest(QUrl(f"{MARKETPLACE_API_URL}{path}"))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, USER_AGENT)
        if hasattr(request, "setTransferTimeout"):  # Qt 6.7+
            request.setTransferTimeout(REQUEST_TIMEOUT_MS)
        return request
