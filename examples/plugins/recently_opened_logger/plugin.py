"""Example plugin: logs every project you open to a per-plugin storage file,
and adds a menu action to view the recent history. Exercises: the
on_project_opened push hook, contribute_menu_actions, ctx.storage_dir, and
ctx.settings.

To try it: copy this folder into your MyAppsLibrary plugins directory (see
paths.plugins_dir()), then enable it from the Plugins menu.
"""

from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtWidgets import QMessageBox

from myapps.plugins.api import PluginBase, PluginContext, PluginMenuAction

DEFAULT_MAX_LINES = 50


class RecentlyOpenedLoggerPlugin(PluginBase):
    def on_load(self, ctx: PluginContext) -> None:
        self._ctx = ctx
        self._log_path = ctx.storage_dir / "recent.log"
        ctx.logger.info("Recently Opened Logger plugin loaded")

    def on_project_opened(self, project_id: str, editor_id: str) -> None:
        project = self._ctx.projects.get_project(project_id)
        name = project.name if project else project_id
        timestamp = datetime.now(UTC).isoformat(timespec="seconds")
        line = f"{timestamp}  {name}  (editor: {editor_id})\n"
        try:
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            self._ctx.logger.exception("Failed to write to %s", self._log_path)

    def contribute_menu_actions(self) -> list[PluginMenuAction]:
        return [PluginMenuAction("Show Recently Opened Log…", self._show_log)]

    def _show_log(self) -> None:
        max_lines = self._ctx.settings.get("max_lines", DEFAULT_MAX_LINES)
        if not self._log_path.exists():
            text = "No projects opened yet."
        else:
            lines = self._log_path.read_text(encoding="utf-8").splitlines()
            text = "\n".join(lines[-max_lines:]) or "No projects opened yet."
        QMessageBox.information(None, "Recently Opened", text)
