# Example plugins

Two minimal plugins demonstrating MyAppsLibrary's plugin API - not installed
by default, and not part of the packaged app.

- **`open_in_terminal/`** - adds "Open in Terminal" to each project's
  right-click menu. Exercises `contribute_project_context_actions` and a
  non-empty `permissions` list.
- **`recently_opened_logger/`** - logs every project you open and adds a
  "Show Recently Opened Log…" item to the Plugins menu. Exercises the
  `on_project_opened` push hook, `contribute_menu_actions`, `ctx.storage_dir`,
  and `ctx.settings`.

## Trying them

Copy either folder into your MyAppsLibrary plugins directory:

```bash
python -c "from myapps.paths import plugins_dir; print(plugins_dir())"
```

then launch the app, open **Plugins → Manage Plugins…**, and enable the
plugin from the list (you'll see a one-time trust disclosure - plugins run
with full app privileges and are not sandboxed).

Or install one directly from this repo without copying by hand:

```python
from myapps.plugins.manager import PluginManager
from myapps.core.project_manager import ProjectManager

pm = ProjectManager()
plugins = PluginManager(pm)
plugins.install_from_path("examples/plugins/open_in_terminal")
```
