"""Tests for the icon-pack and theme-palette extension points:
PluginBase.contribute_icon_packs()/contribute_theme_palettes() ->
PluginManager.collect_icon_packs()/collect_theme_palettes().
"""

from myapps.core.project_manager import ProjectManager
from myapps.plugins.api import IconDef, IconPack, ThemePalette
from myapps.plugins.manager import LoadedPlugin, PluginLoadState, PluginManager
from myapps.plugins.manifest import PluginManifest
from myapps.ui.theme.tokens import default_dark_tokens, default_light_tokens


def make_manager(tmp_path) -> tuple[PluginManager, ProjectManager]:
    pm = ProjectManager(path=tmp_path / "library.json")
    plugins_dir = tmp_path / "plugins"
    manager = PluginManager(
        pm, plugins_dir=plugins_dir, installed_file=plugins_dir / "installed.json"
    )
    return manager, pm


def _load(manager, plugin_id, instance):
    manifest = PluginManifest(id=plugin_id, name=plugin_id, version="1.0.0", entry_point="x:X")
    manager._loaded[plugin_id] = LoadedPlugin(manifest, instance, PluginLoadState.LOADED)


# -- icon packs -----------------------------------------------------------


def test_collect_icon_packs_from_loaded_enabled_plugin(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class IconPlugin:
        state = PluginLoadState.LOADED

        def contribute_icon_packs(self):
            return [IconPack(id="fruits", label="Fruits", icons=[IconDef(id="apple", glyph="🍎")])]

    _load(manager, "icons", IconPlugin())
    result = manager.collect_icon_packs()
    assert len(result) == 1
    assert result[0].id == "fruits"
    assert result[0].icons[0].glyph == "🍎"


def test_collect_icon_packs_excludes_disabled_plugin(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class IconPlugin:
        state = PluginLoadState.DISABLED

        def contribute_icon_packs(self):
            return [IconPack(id="fruits", label="Fruits", icons=[])]

    manifest = PluginManifest(id="icons", name="icons", version="1.0.0", entry_point="x:X")
    manager._loaded["icons"] = LoadedPlugin(manifest, None, PluginLoadState.DISABLED)

    assert manager.collect_icon_packs() == []


def test_collect_icon_packs_raising_plugin_contributes_nothing(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class BadPlugin:
        state = PluginLoadState.LOADED

        def contribute_icon_packs(self):
            raise RuntimeError("boom")

    _load(manager, "bad", BadPlugin())
    assert manager.collect_icon_packs() == []


def test_collect_icon_packs_skips_non_iconpack_values(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class WrongTypePlugin:
        state = PluginLoadState.LOADED

        def contribute_icon_packs(self):
            return ["not-an-iconpack"]

    _load(manager, "wrong", WrongTypePlugin())
    assert manager.collect_icon_packs() == []


def test_collect_icon_packs_concatenates_two_plugins(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class PluginA:
        state = PluginLoadState.LOADED

        def contribute_icon_packs(self):
            return [IconPack(id="a", label="A", icons=[])]

    class PluginB:
        state = PluginLoadState.LOADED

        def contribute_icon_packs(self):
            return [IconPack(id="b", label="B", icons=[])]

    _load(manager, "a", PluginA())
    _load(manager, "b", PluginB())
    result = manager.collect_icon_packs()
    assert {p.id for p in result} == {"a", "b"}


# -- theme palettes ---------------------------------------------------------


def test_collect_theme_palettes_from_loaded_enabled_plugin(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class ThemePlugin:
        state = PluginLoadState.LOADED

        def contribute_theme_palettes(self):
            return [
                ThemePalette(
                    id="ocean",
                    label="Ocean",
                    light=default_light_tokens(),
                    dark=default_dark_tokens(),
                )
            ]

    _load(manager, "theme", ThemePlugin())
    result = manager.collect_theme_palettes()
    assert len(result) == 1
    assert result[0].id == "ocean"


def test_collect_theme_palettes_rejects_incomplete_tokens(tmp_path):
    manager, _pm = make_manager(tmp_path)

    class BadThemePlugin:
        state = PluginLoadState.LOADED

        def contribute_theme_palettes(self):
            return [
                ThemePalette(
                    id="broken",
                    label="Broken",
                    light={"bg": "#000000"},  # missing most required keys
                    dark=default_dark_tokens(),
                )
            ]

    _load(manager, "theme", BadThemePlugin())
    assert manager.collect_theme_palettes() == []


def test_collect_theme_palettes_rejects_non_hex_values(tmp_path):
    manager, _pm = make_manager(tmp_path)
    bad_light = default_light_tokens()
    bad_light["bg"] = "not-a-color"

    class BadThemePlugin:
        state = PluginLoadState.LOADED

        def contribute_theme_palettes(self):
            return [
                ThemePalette(
                    id="broken", label="Broken", light=bad_light, dark=default_dark_tokens()
                )
            ]

    _load(manager, "theme", BadThemePlugin())
    assert manager.collect_theme_palettes() == []


def test_collect_theme_palettes_excludes_disabled_plugin(tmp_path):
    manager, _pm = make_manager(tmp_path)
    manifest = PluginManifest(id="theme", name="theme", version="1.0.0", entry_point="x:X")
    manager._loaded["theme"] = LoadedPlugin(manifest, None, PluginLoadState.DISABLED)

    assert manager.collect_theme_palettes() == []
