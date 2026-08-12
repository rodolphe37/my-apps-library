"""Example plugin: adds an "Open in Terminal" action to each project's
right-click context menu. Exercises: manifest parsing, on_load,
contribute_project_context_actions, and a non-empty permissions list.

To try it: copy this folder into your MyAppsLibrary plugins directory (see
paths.plugins_dir(), typically the platform's app-data dir + "plugins/"),
then enable it from File > Manage Plugins (or the Plugins menu).
"""

from __future__ import annotations

import platform

from myapps.plugins.api import PluginBase, PluginContext, PluginMenuAction
from myapps.utils.process_utils import launch_detached


class OpenInTerminalPlugin(PluginBase):
    def on_load(self, ctx: PluginContext) -> None:
        self._ctx = ctx
        ctx.logger.info("Open in Terminal plugin loaded")

    def contribute_project_context_actions(self, project) -> list[PluginMenuAction]:
        return [PluginMenuAction("Open in Terminal", lambda: self._open(project.path))]

    def _open(self, path: str) -> None:
        system = platform.system()
        if system == "Darwin":
            argv = ["open", "-a", "Terminal", path]
        elif system == "Windows":
            argv = ["cmd.exe", "/K", f"cd /d {path}"]
        else:
            # Best-effort: works on most GTK/X11 desktop environments.
            argv = ["x-terminal-emulator", "--working-directory", path]

        if not launch_detached(argv):
            self._ctx.logger.error("Failed to open terminal at %s", path)
