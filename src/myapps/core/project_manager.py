"""CRUD for projects and categories, backed by a single library.json file."""

from __future__ import annotations

import logging
from pathlib import Path

from myapps.core.events import event_bus
from myapps.core.models import Category, Project
from myapps.core.store import load_json, save_json
from myapps.paths import library_file

logger = logging.getLogger(__name__)


class ProjectManager:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or library_file()
        self._projects: dict[str, Project] = {}
        self._categories: dict[str, Category] = {}
        self._load()

    # -- persistence -----------------------------------------------------

    def _load(self) -> None:
        data = load_json(self._path, default={"projects": [], "categories": []})
        self._projects = {
            p["id"]: Project.from_dict(p) for p in data.get("projects", [])
        }
        self._categories = {
            c["id"]: Category.from_dict(c) for c in data.get("categories", [])
        }

    def _save(self) -> None:
        save_json(
            self._path,
            {
                "projects": [p.to_dict() for p in self._projects.values()],
                "categories": [c.to_dict() for c in self._categories.values()],
            },
        )

    # -- projects ----------------------------------------------------------

    def list_projects(self) -> list[Project]:
        return sorted(self._projects.values(), key=lambda p: (not p.pinned, p.name.lower()))

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def find_by_path(self, path: str) -> Project | None:
        resolved = str(Path(path).expanduser().resolve())
        for p in self._projects.values():
            if p.path == resolved:
                return p
        return None

    def add_project(
        self, path: str, name: str | None = None, categories: list[str] | None = None
    ) -> Project:
        """Add a project by folder path. Returns the existing project if this
        path is already in the library (dedupe-by-path), otherwise creates a
        new one.
        """
        resolved = str(Path(path).expanduser().resolve())
        existing = self.find_by_path(resolved)
        if existing:
            logger.info("Project at %s already in library, skipping duplicate add", resolved)
            return existing

        project = Project(
            name=name or Path(resolved).name,
            path=resolved,
            categories=list(categories or []),
        )
        self._projects[project.id] = project
        self._save()
        event_bus.project_added.emit(project.id)
        return project

    def remove_project(self, project_id: str) -> None:
        """Remove a project from the library. This never touches the folder
        on disk — it only deletes the library reference.
        """
        if project_id in self._projects:
            del self._projects[project_id]
            self._save()
            event_bus.project_removed.emit(project_id)

    def update_project(self, project_id: str, **fields) -> Project | None:
        project = self._projects.get(project_id)
        if project is None:
            return None
        for key, value in fields.items():
            if hasattr(project, key):
                setattr(project, key, value)
        self._save()
        event_bus.project_updated.emit(project_id)
        return project

    def mark_opened(self, project_id: str, editor_id: str) -> None:
        from myapps.core.models import _now_iso  # local import to avoid polluting module top

        self.update_project(project_id, last_opened_at=_now_iso())
        event_bus.project_opened.emit(project_id, editor_id)

    def set_categories(self, project_id: str, category_ids: list[str]) -> None:
        self.update_project(project_id, categories=list(category_ids))

    # -- categories --------------------------------------------------------

    def list_categories(self) -> list[Category]:
        return sorted(self._categories.values(), key=lambda c: (c.order, c.name.lower()))

    def get_category(self, category_id: str) -> Category | None:
        return self._categories.get(category_id)

    def add_category(self, name: str, color: str | None = None) -> Category:
        order = len(self._categories)
        category = Category(name=name, color=color, order=order)
        self._categories[category.id] = category
        self._save()
        event_bus.category_added.emit(category.id)
        return category

    def rename_category(self, category_id: str, name: str) -> None:
        if category_id in self._categories:
            self._categories[category_id].name = name
            self._save()
            event_bus.category_updated.emit(category_id)

    def remove_category(self, category_id: str) -> None:
        """Remove a category and unassign it from any projects that had it."""
        if category_id not in self._categories:
            return
        del self._categories[category_id]
        for project in self._projects.values():
            if category_id in project.categories:
                project.categories.remove(category_id)
        self._save()
        event_bus.category_removed.emit(category_id)

    def projects_in_category(self, category_id: str | None) -> list[Project]:
        """`category_id=None` returns projects with no categories assigned."""
        if category_id is None:
            return [p for p in self.list_projects() if not p.categories]
        return [p for p in self.list_projects() if category_id in p.categories]
