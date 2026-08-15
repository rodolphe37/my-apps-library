"""Advisory trust/permission disclosure - NOT a real sandbox.

Plugins run as regular in-process Python with full application privileges.
True sandboxing (subprocess + IPC isolation) is a large undertaking that's
out of scope for now; this module only produces the disclosure text and
permission descriptions shown to the user before they enable a plugin.

Consumed only by `PluginManagerDialog`, which is freshly instantiated on
each open - so calling `tr()` here at call time (not at import time) is all
that's needed for these strings to stay current with the active language.
"""

from __future__ import annotations

from myapps.i18n import tr
from myapps.plugins.manifest import PluginManifest

# Maps a permission id to its translation key - kept as keys, not
# pre-resolved strings, so the description text is re-looked-up per call
# against whatever language is active at the time (see module docstring).
_PERMISSION_KEYS: dict[str, str] = {
    "process": "plugin.permission.process",
    "network": "plugin.permission.network",
    "filesystem:read": "plugin.permission.filesystem_read",
    "filesystem:write": "plugin.permission.filesystem_write",
    "translations": "plugin.permission.translations",
}


def describe_permissions(manifest: PluginManifest) -> list[str]:
    """Human-readable descriptions for a manifest's declared permissions.
    Unknown permission strings are passed through verbatim so nothing is
    silently hidden from the user."""
    result = []
    for permission in manifest.permissions:
        key = _PERMISSION_KEYS.get(permission)
        result.append(tr(key) if key else tr("plugin.permission.unknown", perm=permission))
    return result


def trust_disclosure_text() -> str:
    return tr("plugin.trust_disclosure")
