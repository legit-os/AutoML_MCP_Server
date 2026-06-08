import pytest
from pathlib import Path 
from dist_automl.managers.projects_manager import ProjectJSON


@pytest.fixture
def temp_manager(tmp_path):
    json_path = tmp_path / "test_projects.json"
    return ProjectJSON(json_path=json_path)



def test_initialization_creates_empty_config(temp_manager):
    projects = temp_manager.list_projects()
    assert projects == []



def test_add_project(temp_manager):
    temp_manager.add_or_update(
        name="TestProject",
        root=Path("/tmp/test_project"),
        metadata={"type": "ml"},
    )

    projects = temp_manager.list_projects()
    assert len(projects) == 1
    assert projects[0].name == "TestProject"



def test_add_duplicate_without_overwrite_raises(temp_manager):
    temp_manager.add_or_update("Proj1", Path("/tmp/proj1"))

    with pytest.raises(ValueError):
        temp_manager.add_or_update("Proj1", Path("/tmp/proj1_new"))


def test_overwrite_project(temp_manager):
    temp_manager.add_or_update("Proj1", Path("/tmp/proj1"))

    temp_manager.add_or_update(
        "Proj1",
        Path("/tmp/proj1_updated"),
        metadata={"version": 2},
        overwrite=True,
    )

    project = temp_manager.list_projects()[0]
    assert project.root == Path("/tmp/proj1_updated")
    assert project.metadata["version"] == 2



def test_delete_project(temp_manager):
    temp_manager.add_or_update("Proj2", Path("/tmp/proj2"))
    temp_manager.delete("Proj2")

    projects = temp_manager.list_projects()
    assert projects == []


def test_delete_nonexistent_raises(temp_manager):
    with pytest.raises(ValueError):
        temp_manager.delete("DoesNotExist")



def test_persistence_across_reload(tmp_path):
    json_path = tmp_path / "persist_test.json"

    manager1 = ProjectJSON(json_path=json_path)
    manager1.add_or_update("PersistentProj", Path("/tmp/persist"))

    manager2 = ProjectJSON(json_path=json_path)
    projects = manager2.list_projects()

    assert len(projects) == 1
    assert projects[0].name == "PersistentProj"