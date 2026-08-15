"""Background check against GitHub's own "latest release" API - the same
source of truth the README's install instructions and the Homebrew cask
point at, so "a newer version is available" always means a real, already-
published release with downloadable assets, never a dangling tag.

Deliberately silent on any failure (offline, GitHub down, unexpected
response shape, rate-limited): this is a nice-to-have notice, never worth
bothering the user with an error dialog over, and never worth blocking
startup on - the request is fully async (QNetworkAccessManager), fired
once after the main window is already up and shown.
"""

from __future__ import annotations

import json
import logging

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from myapps.utils.version_utils import is_newer

logger = logging.getLogger(__name__)

LATEST_RELEASE_API_URL = (
    "https://api.github.com/repos/rodolphe37/my-apps-library/releases/latest"
)
REQUEST_TIMEOUT_MS = 8000


class UpdateChecker(QObject):
    # Emitted with the new version string (no leading "v", e.g. "0.6.1")
    # only when it's actually newer than the version passed to check().
    # Never emitted at all on failure or when already up to date.
    update_available = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Held as an attribute, not a local in check() - QNetworkAccessManager
        # must outlive the request it issues, and a local would be garbage
        # collected (from Python's side; PySide6 doesn't keep it alive for
        # you) before the async reply ever comes back.
        self._manager = QNetworkAccessManager(self)

    def check(self, current_version: str) -> None:
        request = QNetworkRequest(QUrl(LATEST_RELEASE_API_URL))
        # GitHub's REST API 400s a request with no User-Agent at all.
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "MyAppsLibrary-UpdateCheck")
        if hasattr(request, "setTransferTimeout"):  # Qt 6.7+
            request.setTransferTimeout(REQUEST_TIMEOUT_MS)
        reply = self._manager.get(request)
        reply.finished.connect(lambda: self._on_finished(reply, current_version))

    def _on_finished(self, reply: QNetworkReply, current_version: str) -> None:
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            logger.info("Update check failed (network): %s", reply.errorString())
            return
        latest_version = parse_latest_version(bytes(reply.readAll()), current_version)
        if latest_version is not None:
            self.update_available.emit(latest_version)


def parse_latest_version(raw_response: bytes, current_version: str) -> str | None:
    """The pure half of the response handling: given the API's raw JSON
    body, returns the release's version string (no leading "v") if it's
    newer than `current_version`, else None - covers "malformed JSON",
    "missing tag_name", and "not actually newer" all the same way, since
    none of them should ever surface to the user. Separated from
    _on_finished so it's exercisable without a real QNetworkReply (fragile
    to construct by hand in PySide6, same tradeoff noted in
    ui/widgets/context_menu.py's own _handle_drop())."""
    try:
        payload = json.loads(raw_response.decode("utf-8"))
        tag_name = payload["tag_name"]
    except (ValueError, KeyError, UnicodeDecodeError) as exc:
        logger.info("Update check failed (bad response): %s", exc)
        return None

    latest_version = tag_name.removeprefix("v")
    return latest_version if is_newer(latest_version, current_version) else None
