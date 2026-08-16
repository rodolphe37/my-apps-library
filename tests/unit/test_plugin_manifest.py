import pytest

from myapps.plugins.manifest import ManifestError, parse_manifest, parse_min_app_version

VALID_TOML = """
[plugin]
id = "my-plugin"
name = "My Plugin"
version = "1.0.0"
entry_point = "plugin:MyPlugin"
description = "A test plugin"
permissions = ["process"]
tags = ["example"]
"""


def write_manifest(tmp_path, content: str):
    path = tmp_path / "plugin.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_manifest_parses(tmp_path):
    path = write_manifest(tmp_path, VALID_TOML)
    manifest = parse_manifest(path)
    assert manifest.id == "my-plugin"
    assert manifest.name == "My Plugin"
    assert manifest.version == "1.0.0"
    assert manifest.entry_point == "plugin:MyPlugin"
    assert manifest.permissions == ["process"]
    assert manifest.source_dir == tmp_path


@pytest.mark.parametrize("missing_field", ["id", "name", "version", "entry_point"])
def test_missing_required_field_raises(tmp_path, missing_field):
    import tomllib

    data = tomllib.loads(VALID_TOML)
    del data["plugin"][missing_field]
    lines = ["[plugin]"]
    for k, v in data["plugin"].items():
        if isinstance(v, str):
            lines.append(f'{k} = "{v}"')
        else:
            lines.append(f"{k} = {v!r}")
    path = write_manifest(tmp_path, "\n".join(lines))
    with pytest.raises(ManifestError):
        parse_manifest(path)


def test_invalid_id_format_raises(tmp_path):
    path = write_manifest(tmp_path, VALID_TOML.replace('id = "my-plugin"', 'id = "My Plugin!"'))
    with pytest.raises(ManifestError):
        parse_manifest(path)


def test_invalid_entry_point_format_raises(tmp_path):
    path = write_manifest(
        tmp_path, VALID_TOML.replace('entry_point = "plugin:MyPlugin"', 'entry_point = "plugin"')
    )
    with pytest.raises(ManifestError):
        parse_manifest(path)


def test_malformed_toml_raises_manifest_error_not_raw_tomllib_error(tmp_path):
    path = write_manifest(tmp_path, "this is not [valid toml")
    with pytest.raises(ManifestError):
        parse_manifest(path)


def test_missing_plugin_section_raises(tmp_path):
    path = write_manifest(tmp_path, "[other]\nfoo = 1\n")
    with pytest.raises(ManifestError):
        parse_manifest(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(ManifestError):
        parse_manifest(tmp_path / "does-not-exist.toml")


def test_parse_min_app_version():
    assert parse_min_app_version("1.2.3") == (1, 2, 3)
    assert parse_min_app_version("0.1.0") < parse_min_app_version("0.2.0")
    assert parse_min_app_version("1.0") < parse_min_app_version("1.0.1")


def test_icon_defaults_to_none(tmp_path):
    manifest = parse_manifest(write_manifest(tmp_path, VALID_TOML))
    assert manifest.icon is None
    assert manifest.icon_path is None


def test_icon_path_resolves_when_file_exists(tmp_path):
    (tmp_path / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    path = write_manifest(tmp_path, VALID_TOML + '\nicon = "icon.png"\n')
    manifest = parse_manifest(path)
    assert manifest.icon == "icon.png"
    assert manifest.icon_path == (tmp_path / "icon.png").resolve()


def test_icon_path_is_none_when_file_missing(tmp_path):
    # Declared but never actually shipped - fails open (None), not an error.
    path = write_manifest(tmp_path, VALID_TOML + '\nicon = "does-not-exist.png"\n')
    manifest = parse_manifest(path)
    assert manifest.icon == "does-not-exist.png"
    assert manifest.icon_path is None


def test_non_string_icon_raises(tmp_path):
    path = write_manifest(tmp_path, VALID_TOML + "\nicon = 42\n")
    with pytest.raises(ManifestError):
        parse_manifest(path)
