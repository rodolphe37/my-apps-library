import os
import time

from myapps.core.project_manager import ProjectManager
from myapps.ui.models.project_list_model import ProjectIdRole, ProjectListModel


def make_project(pm: ProjectManager, tmp_path, name: str):
    d = tmp_path / name
    d.mkdir()
    return pm.add_project(str(d), name=name)


def names_in_order(model: ProjectListModel) -> list[str]:
    return [model.index(row, 0).data() for row in range(model.rowCount())]


def test_sort_by_name_ascending_and_descending(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    make_project(pm, tmp_path, "charlie")
    make_project(pm, tmp_path, "alpha")
    make_project(pm, tmp_path, "bravo")

    model.set_sort("name", "asc")
    assert names_in_order(model) == ["alpha", "bravo", "charlie"]

    model.set_sort("name", "desc")
    assert names_in_order(model) == ["charlie", "bravo", "alpha"]


def test_sort_by_created_at(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    make_project(pm, tmp_path, "first")
    time.sleep(0.01)
    make_project(pm, tmp_path, "second")
    time.sleep(0.01)
    make_project(pm, tmp_path, "third")

    model.set_sort("created_at", "asc")
    assert names_in_order(model) == ["first", "second", "third"]

    model.set_sort("created_at", "desc")
    assert names_in_order(model) == ["third", "second", "first"]


def test_sort_by_modified_at_uses_filesystem_mtime(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    old = make_project(pm, tmp_path, "old")
    new = make_project(pm, tmp_path, "new")

    now = time.time()
    os.utime(old.path, (now - 1000, now - 1000))
    os.utime(new.path, (now, now))

    model.set_sort("modified_at", "asc")
    assert names_in_order(model) == ["old", "new"]

    model.set_sort("modified_at", "desc")
    assert names_in_order(model) == ["new", "old"]


def test_sort_by_size(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    small = make_project(pm, tmp_path, "small")
    big = make_project(pm, tmp_path, "big")

    (tmp_path / "small" / "a.txt").write_bytes(b"x" * 10)
    (tmp_path / "big" / "a.txt").write_bytes(b"x" * 10_000)

    model.set_sort("size", "asc")
    assert names_in_order(model) == ["small", "big"]

    model.set_sort("size", "desc")
    assert names_in_order(model) == ["big", "small"]
    assert small.id != big.id  # sanity: two distinct projects were compared


def test_pinned_projects_float_to_top_regardless_of_direction(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    make_project(pm, tmp_path, "alpha")
    pinned = make_project(pm, tmp_path, "zulu")
    pm.update_project(pinned.id, pinned=True)

    model.set_sort("name", "asc")
    assert names_in_order(model) == ["zulu", "alpha"]

    model.set_sort("name", "desc")
    assert names_in_order(model) == ["zulu", "alpha"]  # still pinned-first, not flipped


def test_unknown_sort_key_falls_back_to_name(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    make_project(pm, tmp_path, "bravo")
    make_project(pm, tmp_path, "alpha")

    model.set_sort("not-a-real-key", "asc")
    assert names_in_order(model) == ["alpha", "bravo"]


def test_size_is_cached_across_resorts(tmp_path, qtbot, monkeypatch):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    make_project(pm, tmp_path, "solo")

    calls = []
    import myapps.ui.models.project_list_model as module

    real = module.directory_size

    def spy(path):
        calls.append(path)
        return real(path)

    monkeypatch.setattr(module, "directory_size", spy)

    model.set_sort("size", "asc")
    model.set_sort("size", "desc")
    model.set_sort("size", "asc")

    assert len(calls) == 1  # computed once, cached for subsequent re-sorts


def test_project_id_role_still_correct_after_sort(tmp_path, qtbot):
    pm = ProjectManager(path=tmp_path / "library.json")
    model = ProjectListModel(pm)
    a = make_project(pm, tmp_path, "aaa")
    b = make_project(pm, tmp_path, "bbb")

    model.set_sort("name", "desc")
    assert model.index(0, 0).data(ProjectIdRole) == b.id
    assert model.index(1, 0).data(ProjectIdRole) == a.id
