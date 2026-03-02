import pytest
from pathlib import Path

from dist_automl.working_dir.dir_class import WorkingDirectory

def test_init_creates_structure(tmp_path: Path):
    root = tmp_path / "project"
    

    wd = WorkingDirectory(root)

    assert root.exists()
    assert (root / "analysis").exists()
    assert (root / "utils").exists()
    assert (root / "pipeline").exists()
    assert (root / "config.yaml").exists()


def test_init_with_existing_directory(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()

    wd = WorkingDirectory(root)

    
    assert (root / "analysis").exists()
    assert (root / "config.yaml").exists()


def test_update_utils_creates_file_and_yaml(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("utils/helper.py")
    
    wd.update_utils(
        name="helper",
        path=path,
        metadata={"version": 1},
        content="print('hello')",
    )

    assert (root / path).exists()

    entry = wd.config.get("utils.files.helper")
    assert entry["path"] == path.as_posix()

    wd.config.save()
    assert (root / "config.yaml").exists()


def test_delete_utils_removes_file_and_yaml(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("utils/helper.py")

    wd.update_utils(name="helper", path=path)
    wd.delete_utils("helper")

    assert not (root / path).exists()
    assert wd.config.get("utils.files.helper") is None



def test_update_analysis_creates_file(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("analysis/train.py")

    wd.update_analysis(
        name="train",
        path=path,
        output_type="graph",
        content="print('train')",
    )

    assert (root / path).exists()
    entry = wd.config.get("analysis.files.train")
    assert entry["path"] == path.as_posix()


def test_delete_analysis(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("analysis/train.py")

    wd.update_analysis(name="train", path=path)
    wd.delete_analysis("train")

    assert not (root / path).exists()
    assert wd.config.get("analysis.files.train") is None



def test_update_pipeline_element(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("pipeline/stage1/clean.py")

    wd.update_pipeline_element(
        stage="stage1",
        name="clean",
        path=path,
        metadata={"order": 1},
        content="print('clean')",
    )

    assert (root / path).exists()

    entry = wd.config.get("pipeline.stages.stage1.elements.clean")
    assert entry["path"] == path.as_posix()


def test_delete_pipeline_element(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("pipeline/stage1/clean.py")

    wd.update_pipeline_element(
        stage="stage1",
        name="clean",
        path=path,
    )

    wd.delete_pipeline_element("stage1", "clean")

    assert not (root / path).exists()
    assert wd.config.get("pipeline.stages.stage1.elements.clean") is None


def test_absolute_path_normalization(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    abs_path = root / "analysis" / "abs_train.py"

    wd.update_analysis(name="abs_train", path=abs_path)

    assert abs_path.exists()
    entry = wd.config.get("analysis.files.abs_train")
    assert entry["path"] == "analysis/abs_train.py"


def test_reject_outside_root(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    outside = tmp_path / "outside.py"

    with pytest.raises(ValueError):
        wd.update_analysis(name="bad", path=outside)



def test_check_project_sync_detects_missing_file(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("analysis/missing.py")

    wd.update_analysis(name="missing", path=path)

    (root / path).unlink()

    warnings = wd.manager.check_project_sync(root)

    assert len(warnings) > 0


def test_check_project_sync_clean(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    path = Path("analysis/train.py")
    wd.update_analysis(name="train", path=path)

    warnings = wd.manager.check_project_sync(root)
    assert warnings == []


def test_transaction_rollback_on_invalid_path(tmp_path: Path):
    root = tmp_path / "project"
    wd = WorkingDirectory(root)

    bad_path = Path("analysis/train.txt")  

    with pytest.raises(ValueError):
        wd.update_analysis(name="train", path=bad_path)

    assert not (root / "analysis/train.txt").exists()