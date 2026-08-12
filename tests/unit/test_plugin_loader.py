from myapps.plugins.loader import discover_local

VALID_TOML = """
[plugin]
id = "{id}"
name = "{id}"
version = "1.0.0"
entry_point = "plugin:Plugin"
"""


def make_plugin_folder(base, plugin_id, valid=True):
    folder = base / plugin_id
    folder.mkdir()
    if valid:
        (folder / "plugin.toml").write_text(VALID_TOML.format(id=plugin_id), encoding="utf-8")
    else:
        (folder / "plugin.toml").write_text("not valid [toml", encoding="utf-8")
    return folder


def test_discover_local_returns_only_valid_manifests(tmp_path):
    make_plugin_folder(tmp_path, "good-one")
    make_plugin_folder(tmp_path, "good-two")
    make_plugin_folder(tmp_path, "broken-one", valid=False)

    manifests = discover_local(tmp_path)
    ids = {m.id for m in manifests}
    assert ids == {"good-one", "good-two"}


def test_discover_local_never_raises_on_missing_dir(tmp_path):
    assert discover_local(tmp_path / "does-not-exist") == []


def test_discover_local_skips_folders_without_manifest(tmp_path):
    (tmp_path / "not-a-plugin").mkdir()
    (tmp_path / "not-a-plugin" / "readme.txt").write_text("hi", encoding="utf-8")
    assert discover_local(tmp_path) == []


def test_discover_local_ignores_files_at_top_level(tmp_path):
    (tmp_path / "stray.txt").write_text("hi", encoding="utf-8")
    make_plugin_folder(tmp_path, "good-one")
    manifests = discover_local(tmp_path)
    assert [m.id for m in manifests] == ["good-one"]
