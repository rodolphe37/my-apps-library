"""Plain dataclasses for the app's core domain objects.

These are trusted, internally-produced data (unlike plugin manifests, which
will be validated more strictly in Phase 2), so plain dataclasses are enough —
no need for pydantic here.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


def _new_id() -> str:
    return uuid.uuid4().hex


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Category:
    id: str = field(default_factory=_new_id)
    name: str = ""
    color: str | None = None
    order: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Category:
        return cls(
            id=data.get("id", _new_id()),
            name=data.get("name", ""),
            color=data.get("color"),
            order=data.get("order", 0),
        )


@dataclass
class Project:
    id: str = field(default_factory=_new_id)
    name: str = ""
    path: str = ""  # absolute, resolved
    categories: list[str] = field(default_factory=list)  # category ids (many-to-many)
    description: str = ""
    preferred_editor_id: str | None = None
    created_at: str = field(default_factory=_now_iso)
    last_opened_at: str | None = None
    pinned: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        return cls(
            id=data.get("id", _new_id()),
            name=data.get("name", ""),
            path=data.get("path", ""),
            categories=list(data.get("categories", [])),
            description=data.get("description", ""),
            preferred_editor_id=data.get("preferred_editor_id"),
            created_at=data.get("created_at", _now_iso()),
            last_opened_at=data.get("last_opened_at"),
            pinned=data.get("pinned", False),
        )


@dataclass
class AppSettings:
    theme_mode: str = "system"  # "system" | "light" | "dark"
    language: str = "system"  # "system" | "en" | "fr" | <plugin-provided locale code>
    view_mode: str = "list"
    global_default_editor_id: str | None = None
    window_geometry: str | None = None  # base64 QByteArray, stored as text
    sidebar_visible: bool = True
    last_selected_category: str | None = None  # None = "All"
    # "name" | "created_at" | "modified_at" | "size" — see
    # ui/models/project_list_model.py::ProjectListModel.set_sort().
    sort_key: str = "name"
    sort_direction: str = "asc"  # "asc" | "desc"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AppSettings:
        defaults = cls()
        return cls(
            theme_mode=data.get("theme_mode", defaults.theme_mode),
            language=data.get("language", defaults.language),
            view_mode=data.get("view_mode", defaults.view_mode),
            global_default_editor_id=data.get("global_default_editor_id"),
            window_geometry=data.get("window_geometry"),
            sidebar_visible=data.get("sidebar_visible", True),
            last_selected_category=data.get("last_selected_category"),
            sort_key=data.get("sort_key", defaults.sort_key),
            sort_direction=data.get("sort_direction", defaults.sort_direction),
        )
