from myapps.core.project_manager import ProjectManager


def make_pm(tmp_path):
    return ProjectManager(path=tmp_path / "library.json")


def test_add_project_creates_entry(tmp_path):
    pm = make_pm(tmp_path)
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    project = pm.add_project(str(project_dir))
    assert project.name == "myproj"
    assert project.path == str(project_dir.resolve())
    assert len(pm.list_projects()) == 1


def test_add_project_dedupes_by_path(tmp_path):
    pm = make_pm(tmp_path)
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    first = pm.add_project(str(project_dir))
    second = pm.add_project(str(project_dir))
    assert first.id == second.id
    assert len(pm.list_projects()) == 1


def test_remove_project_does_not_delete_folder(tmp_path):
    pm = make_pm(tmp_path)
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    project = pm.add_project(str(project_dir))
    pm.remove_project(project.id)
    assert pm.get_project(project.id) is None
    assert project_dir.exists()  # folder on disk is untouched


def test_category_assignment_many_to_many(tmp_path):
    pm = make_pm(tmp_path)
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    project = pm.add_project(str(project_dir))
    cat_a = pm.add_category("Python")
    cat_b = pm.add_category("Client X")

    pm.set_categories(project.id, [cat_a.id, cat_b.id])
    reloaded = pm.get_project(project.id)
    assert set(reloaded.categories) == {cat_a.id, cat_b.id}
    assert reloaded in pm.projects_in_category(cat_a.id)
    assert reloaded in pm.projects_in_category(cat_b.id)


def test_remove_category_unassigns_from_projects(tmp_path):
    pm = make_pm(tmp_path)
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    project = pm.add_project(str(project_dir))
    cat = pm.add_category("Python")
    pm.set_categories(project.id, [cat.id])

    pm.remove_category(cat.id)
    reloaded = pm.get_project(project.id)
    assert cat.id not in reloaded.categories
    assert pm.get_category(cat.id) is None


def test_projects_in_category_none_returns_uncategorized(tmp_path):
    pm = make_pm(tmp_path)
    dir_a = tmp_path / "a"
    dir_a.mkdir()
    dir_b = tmp_path / "b"
    dir_b.mkdir()
    project_a = pm.add_project(str(dir_a))
    pm.add_project(str(dir_b))
    cat = pm.add_category("Python")
    pm.set_categories(project_a.id, [cat.id])

    uncategorized = pm.projects_in_category(None)
    assert len(uncategorized) == 1
    assert uncategorized[0].path == str(dir_b.resolve())


def test_persistence_across_instances(tmp_path):
    path = tmp_path / "library.json"
    pm1 = ProjectManager(path=path)
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    project = pm1.add_project(str(project_dir))

    pm2 = ProjectManager(path=path)
    reloaded = pm2.get_project(project.id)
    assert reloaded is not None
    assert reloaded.path == project.path
