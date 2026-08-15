"""Dotted-numeric version parsing/comparison, shared by the plugin manifest's
min_app_version check (plugins/manifest.py) and the update checker
(core/update_checker.py) - two independent uses of the exact same "is X
newer than Y" question, previously only implemented for the first one.
"""

from __future__ import annotations


def parse_version(version: str) -> tuple[int, ...]:
    """Hand-rolled dotted-numeric version compare (no `packaging` dependency
    needed for this narrow use). Non-numeric segments compare as 0."""
    parts = []
    for segment in version.split("."):
        try:
            parts.append(int(segment))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer(candidate: str, baseline: str) -> bool:
    """True if `candidate` (e.g. a GitHub release tag) is a strictly newer
    version than `baseline` (e.g. this build's own constants.VERSION)."""
    return parse_version(candidate) > parse_version(baseline)
