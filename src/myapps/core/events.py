"""Central Qt-signal event bus.

UI widgets connect to these signals to stay in sync with the data layer.
This is also the seam PluginManager (src/myapps/plugins/manager.py) taps into
to dispatch `on_project_added` / `on_project_removed` / `on_project_opened`
hooks without ProjectManager needing to know plugins exist.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    project_added = Signal(str)  # project_id
    project_removed = Signal(str)  # project_id
    project_updated = Signal(str)  # project_id
    project_opened = Signal(str, str)  # project_id, editor_id

    category_added = Signal(str)  # category_id
    category_removed = Signal(str)  # category_id
    category_updated = Signal(str)  # category_id

    settings_changed = Signal(str)  # field name that changed

    editors_refreshed = Signal()

    # Emitted by PluginManager after install/uninstall/enable/disable, so
    # MainWindow and PluginManagerDialog know to rebuild plugin-derived UI.
    plugins_changed = Signal()


# Single shared instance for the whole app.
event_bus = EventBus()
