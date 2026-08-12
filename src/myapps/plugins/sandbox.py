"""Advisory trust/permission disclosure — NOT a real sandbox.

Plugins run as regular in-process Python with full application privileges.
True sandboxing (subprocess + IPC isolation) is a large undertaking that's
out of scope for now; this module only produces the disclosure text and
permission descriptions shown to the user before they enable a plugin.
"""

from __future__ import annotations

from myapps.plugins.manifest import PluginManifest

KNOWN_PERMISSIONS: dict[str, str] = {
    "process": "Can launch other applications or scripts on your computer.",
    "network": "Can make network requests.",
    "filesystem:read": "Can read files outside the app's own data folder.",
    "filesystem:write": "Can write files outside the app's own data folder.",
}


def describe_permissions(manifest: PluginManifest) -> list[str]:
    """Human-readable descriptions for a manifest's declared permissions.
    Unknown permission strings are passed through verbatim so nothing is
    silently hidden from the user."""
    return [KNOWN_PERMISSIONS.get(p, f"Unknown permission: {p!r}") for p in manifest.permissions]


def trust_disclosure_text() -> str:
    return (
        "Plugins run with the same privileges as MyAppsLibrary itself and are "
        "not sandboxed. Only install and enable plugins from sources you trust."
    )
