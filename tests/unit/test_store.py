from myapps.core.store import load_json, save_json


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "data.json"
    save_json(path, {"foo": "bar", "n": 42})
    loaded = load_json(path, default={})
    assert loaded["foo"] == "bar"
    assert loaded["n"] == 42
    assert "schema_version" in loaded


def test_load_missing_file_returns_default(tmp_path):
    path = tmp_path / "missing.json"
    default = {"projects": []}
    assert load_json(path, default=default) == default


def test_load_corrupt_file_quarantines_and_returns_default(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{not valid json", encoding="utf-8")
    result = load_json(path, default={"x": 1})
    assert result == {"x": 1}
    assert (tmp_path / "data.json.corrupt").exists()
    assert not path.exists()


def test_save_survives_no_shell_injection_in_values(tmp_path):
    path = tmp_path / "data.json"
    tricky = {"name": "a\"; rm -rf /; echo \""}
    save_json(path, tricky)
    loaded = load_json(path, default={})
    assert loaded["name"] == tricky["name"]
