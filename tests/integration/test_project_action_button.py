"""End-to-end coverage for the contribute_project_action_button hook: a
plugin contributes a button -> ProjectItemDelegate paints/hit-tests it in
both List and Grid -> ProjectListView.mousePressEvent() detects a click
inside its rect -> MainWindow._on_project_action_button() re-resolves and
invokes the plugin's on_click(). Mirrors test_view_external_drop.py's
make_window() helper and its own note on avoiding hand-built QMouseEvent -
qtbot.mouseClick() constructs a real one instead.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyleOptionViewItem

from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.plugins.api import PluginBase, ProjectActionButton
from myapps.plugins.manager import LoadedPlugin, PluginLoadState, PluginManager
from myapps.plugins.manifest import PluginManifest
from myapps.ui.main_window import MainWindow
from myapps.ui.theme.theme_manager import ThemeManager


def make_window_with_plugin(tmp_path, qtbot, qapp, plugin_instance):
    pm = ProjectManager(path=tmp_path / "library.json")
    sm = SettingsManager(path=tmp_path / "settings.json")
    er = EditorRegistry(path=tmp_path / "editors.json")
    tm = ThemeManager(qapp)
    plugins_dir = tmp_path / "plugins"
    plugin_manager = PluginManager(
        pm, plugins_dir=plugins_dir, installed_file=plugins_dir / "installed.json"
    )
    manifest = PluginManifest(id="runner", name="runner", version="1.0.0", entry_point="x:A")
    loaded = LoadedPlugin(manifest, plugin_instance, PluginLoadState.LOADED)
    plugin_manager._loaded["runner"] = loaded

    window = MainWindow(pm, sm, er, tm, plugin_manager=plugin_manager)
    qtbot.addWidget(window)
    return window, pm


def test_clicking_action_button_invokes_plugin_callback(tmp_path, qtbot, qapp):
    clicks = []

    class RunnerPlugin(PluginBase):
        def contribute_project_action_button(self, project):
            return ProjectActionButton(glyph="▶", on_click=lambda: clicks.append(project.id))

    window, pm = make_window_with_plugin(tmp_path, qtbot, qapp, RunnerPlugin())
    folder = tmp_path / "demo-project"
    folder.mkdir()
    project = pm.add_project(str(folder))

    for mode_id in ("list", "grid"):
        clicks.clear()
        view = window._views[mode_id]
        view.itemDelegate().display_mode = "row" if mode_id == "list" else "tile"
        window._set_active_view_mode(mode_id)

        index = window._model.index(0, 0)
        assert index.isValid()
        view_rect = view.visualRect(index)
        option = QStyleOptionViewItem()
        view.initViewItemOption(option)
        option.rect = view_rect
        button_rect = view.itemDelegate().action_button_rect(option, index)
        assert button_rect is not None, f"no action button hit-rect in {mode_id} mode"

        qtbot.mouseClick(
            view.viewport(), Qt.MouseButton.LeftButton, pos=button_rect.center()
        )

        assert clicks == [project.id], f"click on the {mode_id} action button had no effect"


def test_no_action_button_when_no_plugin_contributes_one(tmp_path, qtbot, qapp):
    class SilentPlugin(PluginBase):
        pass

    window, pm = make_window_with_plugin(tmp_path, qtbot, qapp, SilentPlugin())
    folder = tmp_path / "demo-project"
    folder.mkdir()
    pm.add_project(str(folder))

    view = window._views["list"]
    index = window._model.index(0, 0)
    option = QStyleOptionViewItem()
    view.initViewItemOption(option)
    option.rect = view.visualRect(index)
    assert view.itemDelegate().action_button_rect(option, index) is None
