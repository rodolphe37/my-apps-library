from myapps.editors.registry import EditorRegistry


def test_add_manual_editor_persists(tmp_path):
    path = tmp_path / "editors.json"
    registry = EditorRegistry(path=path)
    editor = registry.add_manual_editor("My Editor", "/usr/local/bin/myeditor")
    assert editor.kind == "manual"

    reloaded = EditorRegistry(path=path)
    editors = reloaded.list_editors()
    assert any(e.id == editor.id and e.display_name == "My Editor" for e in editors)


def test_remove_manual_editor(tmp_path):
    registry = EditorRegistry(path=tmp_path / "editors.json")
    editor = registry.add_manual_editor("My Editor", "/usr/local/bin/myeditor")
    registry.remove_manual_editor(editor.id)
    assert registry.get_editor(editor.id) is None


def test_refresh_preserves_manual_entries(tmp_path, monkeypatch):
    registry = EditorRegistry(path=tmp_path / "editors.json")
    manual = registry.add_manual_editor("My Editor", "/usr/local/bin/myeditor")

    monkeypatch.setattr(EditorRegistry, "_detect_for_current_os", staticmethod(lambda: []))
    registry.refresh()

    assert registry.get_editor(manual.id) is not None


def test_launch_unknown_editor_returns_false(tmp_path):
    registry = EditorRegistry(path=tmp_path / "editors.json")
    assert registry.launch("does-not-exist", "/some/path") is False


def test_launch_replaces_path_placeholder(tmp_path, monkeypatch):
    registry = EditorRegistry(path=tmp_path / "editors.json")
    editor = registry.add_manual_editor("My Editor", "/usr/local/bin/myeditor")

    captured = {}

    def fake_launch_detached(argv):
        captured["argv"] = argv
        return True

    monkeypatch.setattr("myapps.editors.registry.launch_detached", fake_launch_detached)
    assert registry.launch(editor.id, "/some/project") is True
    assert captured["argv"] == ["/usr/local/bin/myeditor", "/some/project"]
