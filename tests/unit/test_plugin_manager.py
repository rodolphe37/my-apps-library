import zipfile

import pytest

from myapps.core.project_manager import ProjectManager
from myapps.plugins.api import PluginBase, PluginMenuAction
from myapps.plugins.manager import (
    LoadedPlugin,
    PluginInstallError,
    PluginLoadState,
    PluginManager,
)
from myapps.plugins.manifest import PluginManifest

GOOD_PLUGIN_TOML = """
[plugin]
id = "{id}"
name = "{id}"
version = "1.0.0"
entry_point = "plugin:{class_name}"
"""

GOOD_PLUGIN_PY = """
from myapps.plugins.api import PluginBase, PluginMenuAction

class {class_name}(PluginBase):
    loaded_flag = []

    def on_load(self, ctx):
        {class_name}.loaded_flag.append(ctx.plugin_id)

    def contribute_menu_actions(self):
        return [PluginMenuAction("Do Thing", lambda: None)]
"""

RAISING_PLUGIN_PY = """
from myapps.plugins.api import PluginBase

class {class_name}(PluginBase):
    def on_load(self, ctx):
        raise RuntimeError("boom")
"""

# A "v2" of GOOD_PLUGIN_PY - same plugin id, different version and a
# differently-labeled menu action, so a test can prove update_from_path()
# actually swapped in the new code (not just the version string) by
# checking which label comes back from collect_menu_actions().
UPDATED_PLUGIN_TOML = """
[plugin]
id = "{id}"
name = "{id}"
version = "2.0.0"
entry_point = "plugin:{class_name}"
"""

UPDATED_PLUGIN_PY = """
from myapps.plugins.api import PluginBase, PluginMenuAction

class {class_name}(PluginBase):
    def contribute_menu_actions(self):
        return [PluginMenuAction("Do New Thing", lambda: None)]
"""


def write_plugin(plugins_dir, plugin_id, class_name, py_source):
    folder = plugins_dir / plugin_id
    folder.mkdir(parents=True)
    (folder / "plugin.toml").write_text(
        GOOD_PLUGIN_TOML.format(id=plugin_id, class_name=class_name), encoding="utf-8"
    )
    (folder / "plugin.py").write_text(py_source.format(class_name=class_name), encoding="utf-8")
    return folder


def write_updated_plugin(tmp_path, plugin_id, class_name):
    folder = tmp_path / f"{plugin_id}-v2-source"
    folder.mkdir(parents=True)
    (folder / "plugin.toml").write_text(
        UPDATED_PLUGIN_TOML.format(id=plugin_id, class_name=class_name), encoding="utf-8"
    )
    (folder / "plugin.py").write_text(
        UPDATED_PLUGIN_PY.format(class_name=class_name), encoding="utf-8"
    )
    return folder


def make_manager(tmp_path) -> tuple[PluginManager, ProjectManager]:
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins_dir = tmp_path / "plugins"
    manager = PluginManager(
        pm, plugins_dir=plugins_dir, installed_file=plugins_dir / "installed.json"
    )
    return manager, pm


def test_load_success_path(tmp_path):
    manager, _pm = make_manager(tmp_path)
    write_plugin(tmp_path / "plugins", "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)

    manifests = manager.discover()
    assert len(manifests) == 1
    loaded = manager.load(manifests[0])

    assert loaded.state == PluginLoadState.LOADED
    assert loaded.instance is not None
    assert loaded.error is None


def test_load_isolation_bad_plugin_does_not_block_good_one(tmp_path):
    manager, _pm = make_manager(tmp_path)
    write_plugin(tmp_path / "plugins", "bad-plugin", "BadPlugin", RAISING_PLUGIN_PY)
    write_plugin(tmp_path / "plugins", "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)

    manifests = {m.id: m for m in manager.discover()}
    bad_result = manager.load(manifests["bad-plugin"])
    good_result = manager.load(manifests["good-plugin"])

    assert bad_result.state == PluginLoadState.FAILED
    assert bad_result.error is not None
    assert "boom" in bad_result.error

    assert good_result.state == PluginLoadState.LOADED
    assert good_result.instance is not None


def test_dispatch_isolation_one_plugin_raising_does_not_stop_others(tmp_path):
    manager, _pm = make_manager(tmp_path)

    calls = []

    class RaisingPlugin(PluginBase):
        def on_project_added(self, project_id):
            raise RuntimeError("kaboom")

    class WellBehavedPlugin(PluginBase):
        def on_project_added(self, project_id):
            calls.append(project_id)

    manifest_a = PluginManifest(id="a", name="a", version="1.0.0", entry_point="x:A")
    manifest_b = PluginManifest(id="b", name="b", version="1.0.0", entry_point="x:B")
    manager._loaded["a"] = LoadedPlugin(manifest_a, RaisingPlugin(), PluginLoadState.LOADED)
    manager._loaded["b"] = LoadedPlugin(manifest_b, WellBehavedPlugin(), PluginLoadState.LOADED)

    manager.dispatch_project_added("proj-1")

    assert calls == ["proj-1"]


def test_enable_disable_persists_across_instances(tmp_path):
    manager, _pm = make_manager(tmp_path)
    write_plugin(tmp_path / "plugins", "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)
    manager.load_all_enabled()  # registers as installed, disabled by default

    manager.enable("good-plugin")
    assert manager._installed["good-plugin"].enabled is True

    manager2, _pm2 = make_manager(tmp_path)
    assert manager2._installed["good-plugin"].enabled is True

    manager2.disable("good-plugin")
    manager3, _pm3 = make_manager(tmp_path)
    assert manager3._installed["good-plugin"].enabled is False


def test_install_from_folder(tmp_path):
    manager, _pm = make_manager(tmp_path)
    source = tmp_path / "source-plugin"
    write_plugin(tmp_path, "source-plugin", "SourcePlugin", GOOD_PLUGIN_PY)
    # write_plugin writes into tmp_path/source-plugin already, `source` points there
    manifest = manager.install_from_path(source)

    assert manifest.id == "source-plugin"
    assert "source-plugin" in manager._installed
    assert manager._installed["source-plugin"].enabled is False
    assert (tmp_path / "plugins" / "source-plugin" / "plugin.toml").exists()


def test_install_from_zip(tmp_path):
    manager, _pm = make_manager(tmp_path)
    folder = write_plugin(tmp_path, "zip-plugin", "ZipPlugin", GOOD_PLUGIN_PY)

    zip_path = tmp_path / "zip-plugin.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in folder.rglob("*"):
            zf.write(file, file.relative_to(folder.parent))

    manifest = manager.install_from_path(zip_path)
    assert manifest.id == "zip-plugin"
    assert (tmp_path / "plugins" / "zip-plugin" / "plugin.toml").exists()


def test_install_invalid_manifest_leaves_no_partial_directory(tmp_path):
    manager, _pm = make_manager(tmp_path)
    bad_folder = tmp_path / "bad-source"
    bad_folder.mkdir()
    (bad_folder / "plugin.toml").write_text("not valid [toml", encoding="utf-8")

    with pytest.raises(PluginInstallError):
        manager.install_from_path(bad_folder)

    assert not (tmp_path / "plugins" / "bad-source").exists()
    assert list((tmp_path / "plugins").glob(".tmp-*")) == []


def test_install_duplicate_id_raises_without_overwriting(tmp_path):
    manager, _pm = make_manager(tmp_path)
    source = write_plugin(tmp_path, "dup-plugin", "DupPlugin", GOOD_PLUGIN_PY)
    manager.install_from_path(source)

    with pytest.raises(PluginInstallError):
        manager.install_from_path(source)


def test_update_from_path_bumps_version_and_replaces_files(tmp_path):
    manager, _pm = make_manager(tmp_path)
    source = write_plugin(tmp_path, "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)
    manager.install_from_path(source)
    assert manager._installed["good-plugin"].version == "1.0.0"

    update_source = write_updated_plugin(tmp_path, "good-plugin", "GoodPlugin")
    manifest = manager.update_from_path(update_source)

    assert manifest.version == "2.0.0"
    assert manager._installed["good-plugin"].version == "2.0.0"
    installed_toml = (tmp_path / "plugins" / "good-plugin" / "plugin.toml").read_text()
    assert 'version = "2.0.0"' in installed_toml


def test_update_preserves_enabled_state(tmp_path):
    manager, _pm = make_manager(tmp_path)
    source = write_plugin(tmp_path, "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)
    manager.install_from_path(source)
    manager.enable("good-plugin")
    assert manager._installed["good-plugin"].enabled is True

    update_source = write_updated_plugin(tmp_path, "good-plugin", "GoodPlugin")
    manager.update_from_path(update_source)

    assert manager._installed["good-plugin"].enabled is True
    assert manager._loaded["good-plugin"].state == PluginLoadState.LOADED


def test_update_preserves_disabled_state(tmp_path):
    manager, _pm = make_manager(tmp_path)
    source = write_plugin(tmp_path, "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)
    manager.install_from_path(source)
    assert manager._installed["good-plugin"].enabled is False

    update_source = write_updated_plugin(tmp_path, "good-plugin", "GoodPlugin")
    manager.update_from_path(update_source)

    assert manager._installed["good-plugin"].enabled is False


def test_update_reloads_enabled_plugin_with_new_code(tmp_path):
    """Not just the version string changing - the actual running code
    (checked here via a menu action whose label differs between v1/v2)
    reflects the new plugin.py, no restart simulated or needed."""
    manager, _pm = make_manager(tmp_path)
    source = write_plugin(tmp_path, "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)
    manager.install_from_path(source)
    manager.enable("good-plugin")
    assert [a.label for a in manager.collect_menu_actions()] == ["Do Thing"]

    update_source = write_updated_plugin(tmp_path, "good-plugin", "GoodPlugin")
    manager.update_from_path(update_source)

    assert [a.label for a in manager.collect_menu_actions()] == ["Do New Thing"]


def test_update_unknown_plugin_raises(tmp_path):
    manager, _pm = make_manager(tmp_path)
    source = write_plugin(tmp_path, "never-installed", "NeverInstalled", GOOD_PLUGIN_PY)

    with pytest.raises(PluginInstallError):
        manager.update_from_path(source)


def test_update_invalid_manifest_leaves_existing_install_untouched(tmp_path):
    manager, _pm = make_manager(tmp_path)
    source = write_plugin(tmp_path, "good-plugin", "GoodPlugin", GOOD_PLUGIN_PY)
    manager.install_from_path(source)

    bad_source = tmp_path / "bad-update-source"
    bad_source.mkdir()
    (bad_source / "plugin.toml").write_text("not valid [toml", encoding="utf-8")

    with pytest.raises(PluginInstallError):
        manager.update_from_path(bad_source)

    assert manager._installed["good-plugin"].version == "1.0.0"
    assert (tmp_path / "plugins" / "good-plugin" / "plugin.toml").exists()


def test_collect_menu_actions_only_returns_loaded_enabled_plugins(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class ContributingPlugin(PluginBase):
        def contribute_menu_actions(self):
            return [PluginMenuAction("Loaded Action", lambda: None)]

    loaded_manifest = PluginManifest(id="loaded", name="loaded", version="1.0.0", entry_point="x:A")
    disabled_manifest = PluginManifest(
        id="disabled", name="disabled", version="1.0.0", entry_point="x:B"
    )
    manager._loaded["loaded"] = LoadedPlugin(
        loaded_manifest, ContributingPlugin(), PluginLoadState.LOADED
    )
    manager._loaded["disabled"] = LoadedPlugin(disabled_manifest, None, PluginLoadState.DISABLED)

    actions = manager.collect_menu_actions()
    assert [a.label for a in actions] == ["Loaded Action"]
