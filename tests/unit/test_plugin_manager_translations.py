"""Tests for the translation-plugin extension point:
PluginBase.contribute_translations() -> PluginManager.collect_translations().
"""

import pytest

from myapps.core.project_manager import ProjectManager
from myapps.plugins.manager import LoadedPlugin, PluginLoadState, PluginManager
from myapps.plugins.manifest import ManifestError, PluginManifest, parse_manifest

TRANSLATION_PLUGIN_TOML = """
[plugin]
id = "{id}"
name = "{id}"
version = "1.0.0"
entry_point = "plugin:{class_name}"
provides_locales = ["de"]
"""

TRANSLATION_PLUGIN_PY = """
from myapps.plugins.api import PluginBase

class {class_name}(PluginBase):
    def contribute_translations(self):
        return {{"de": {{"meta.language_name": "Deutsch", "menu.file.quit": "Beenden"}}}}
"""

RAISING_TRANSLATION_PLUGIN_PY = """
from myapps.plugins.api import PluginBase

class {class_name}(PluginBase):
    def contribute_translations(self):
        raise RuntimeError("boom")
"""


def write_plugin(plugins_dir, plugin_id, class_name, toml_source, py_source):
    folder = plugins_dir / plugin_id
    folder.mkdir(parents=True)
    (folder / "plugin.toml").write_text(
        toml_source.format(id=plugin_id, class_name=class_name), encoding="utf-8"
    )
    (folder / "plugin.py").write_text(py_source.format(class_name=class_name), encoding="utf-8")
    return folder


def make_manager(tmp_path) -> tuple[PluginManager, ProjectManager]:
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins_dir = tmp_path / "plugins"
    manager = PluginManager(
        pm, plugins_dir=plugins_dir, installed_file=plugins_dir / "installed.json"
    )
    return manager, pm


def test_collect_translations_from_loaded_enabled_plugin(tmp_path):
    manager, _pm = make_manager(tmp_path)
    write_plugin(
        tmp_path / "plugins",
        "de-plugin",
        "DePlugin",
        TRANSLATION_PLUGIN_TOML,
        TRANSLATION_PLUGIN_PY,
    )
    manifest = manager.discover()[0]
    manager.load(manifest)

    result = manager.collect_translations()
    assert result == {"de": {"meta.language_name": "Deutsch", "menu.file.quit": "Beenden"}}


def test_collect_translations_excludes_disabled_plugin(tmp_path):
    manager, _pm = make_manager(tmp_path)
    write_plugin(
        tmp_path / "plugins",
        "de-plugin",
        "DePlugin",
        TRANSLATION_PLUGIN_TOML,
        TRANSLATION_PLUGIN_PY,
    )
    manager.load_all_enabled()  # discovered but not enabled -> DISABLED state

    assert manager.collect_translations() == {}


def test_collect_translations_raising_plugin_contributes_nothing_but_does_not_crash(tmp_path):
    manager, _pm = make_manager(tmp_path)
    write_plugin(
        tmp_path / "plugins",
        "bad-de-plugin",
        "BadDePlugin",
        TRANSLATION_PLUGIN_TOML,
        RAISING_TRANSLATION_PLUGIN_PY,
    )
    manifest = manager.discover()[0]
    manager.load(manifest)

    assert manager.collect_translations() == {}


def test_collect_translations_merges_two_plugins_last_writer_wins(tmp_path):
    manager, _pm = make_manager(tmp_path)

    manifest_a = PluginManifest(id="a", name="a", version="1.0.0", entry_point="x:A")
    manifest_b = PluginManifest(id="b", name="b", version="1.0.0", entry_point="x:B")

    class PluginA:
        state = PluginLoadState.LOADED

        def contribute_translations(self):
            return {"de": {"menu.file.quit": "Beenden", "menu.file": "&Datei"}}

    class PluginB:
        state = PluginLoadState.LOADED

        def contribute_translations(self):
            return {"de": {"menu.file.quit": "Verlassen"}}  # collides with A's key

    manager._loaded["a"] = LoadedPlugin(manifest_a, PluginA(), PluginLoadState.LOADED)
    manager._loaded["b"] = LoadedPlugin(manifest_b, PluginB(), PluginLoadState.LOADED)

    result = manager.collect_translations()
    assert result["de"]["menu.file"] == "&Datei"  # only A contributed this key
    assert result["de"]["menu.file.quit"] == "Verlassen"  # B loaded after A, wins the collision


def test_provides_locales_parses_from_manifest(tmp_path):
    folder = write_plugin(
        tmp_path, "de-plugin", "DePlugin", TRANSLATION_PLUGIN_TOML, TRANSLATION_PLUGIN_PY
    )
    manifest = parse_manifest(folder / "plugin.toml")
    assert manifest.provides_locales == ["de"]


def test_provides_locales_defaults_to_empty_list(tmp_path):
    toml_no_locales = """
[plugin]
id = "plain"
name = "plain"
version = "1.0.0"
entry_point = "plugin:Plain"
"""
    path = tmp_path / "plugin.toml"
    path.write_text(toml_no_locales, encoding="utf-8")
    manifest = parse_manifest(path)
    assert manifest.provides_locales == []


def test_provides_locales_must_be_list_of_strings(tmp_path):
    bad_toml = """
[plugin]
id = "plain"
name = "plain"
version = "1.0.0"
entry_point = "plugin:Plain"
provides_locales = "de"
"""
    path = tmp_path / "plugin.toml"
    path.write_text(bad_toml, encoding="utf-8")
    with pytest.raises(ManifestError):
        parse_manifest(path)
