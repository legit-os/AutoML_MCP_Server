import pytest
from pathlib import Path

from dist_automl.working_dir.yaml_class import YamlConfig, YamlManager 


@pytest.fixture
def config(tmp_path):
    config_path = tmp_path / "project.yaml"
    return YamlConfig(config_path)


@pytest.fixture
def manager(config):
    return YamlManager(config)


def test_yaml_config_basic_update_and_save(config):
    config.update("a.b.c", 10)
    config.save()

    assert config.get("a.b.c") == 10


def test_yaml_config_rollback(config):
    config.update("test.value", 123)
    config.rollback()

    assert config.get("test.value") is None


def test_yaml_config_transaction_rollback_on_exception(config):
    with pytest.raises(ValueError):
        with config:
            config.update("x.y", 5)
            raise ValueError("fail")

    assert config.get("x.y") is None


def test_update_utils(manager):
    manager.update_utils("helpers", Path("utils/helpers.py"))
    manager._config.save()

    assert manager._config.get("utils.files.helpers.path") == "utils/helpers.py"


def test_delete_utils(manager):
    manager.update_utils("helpers", Path("utils/helpers.py"))
    manager._config.save()

    manager.delete_utils("helpers")
    manager._config.save()

    assert manager._config.get("utils.files.helpers") is None



def test_update_analysis(manager):
    manager.update_analysis(
        name="summary",
        path=Path("analysis/summary.py"),
        output_type="table",
    )
    manager._config.save()

    assert manager._config.get("analysis.files.summary.output_type") == "table"


def test_delete_analysis(manager):
    manager.update_analysis(
        name="summary",
        path=Path("analysis/summary.py"),
        output_type="table",
    )
    manager._config.save()

    manager.delete_analysis("summary")
    manager._config.save()

    assert manager._config.get("analysis.files.summary") is None


def test_add_pipeline_element(manager):
    manager.update_pipeline(
        stage="preprocessing",
        name="clean_data",
        path=Path("src/preprocess.py"),
    )
    manager._config.save()

    assert manager._config.get(
        "pipeline.stages.preprocessing.elements.clean_data.path"
    ) == "src/preprocess.py"


def test_pipeline_dependency_on_existing_element(manager):
    manager.update_pipeline(
        stage="preprocessing",
        name="clean_data",
        path=Path("src/preprocess.py"),
    )

    manager.update_pipeline(
        stage="training",
        name="train_model",
        path=Path("src/train.py"),
        depends_on=["preprocessing.clean_data"],
    )

    manager._config.save()

    deps = manager._config.get(
        "pipeline.stages.training.elements.train_model.depends_on"
    )

    assert deps == ["preprocessing.clean_data"]


def test_pipeline_dependency_on_utils(manager):
    manager.update_utils("helpers", Path("utils/helpers.py"))

    manager.update_pipeline(
        stage="training",
        name="train_model",
        path=Path("src/train.py"),
        depends_on=["utils.helpers"],
    )

    manager._config.save()

    deps = manager._config.get(
        "pipeline.stages.training.elements.train_model.depends_on"
    )

    assert deps == ["utils.helpers"]


def test_pipeline_reject_missing_dependency(manager):
    with pytest.raises(ValueError):
        manager.update_pipeline(
            stage="training",
            name="train_model",
            path=Path("src/train.py"),
            depends_on=["preprocessing.clean_data"],
        )


def test_pipeline_reject_self_dependency(manager):
    manager.update_pipeline(
        stage="training",
        name="train_model",
        path=Path("src/train.py"),
    )

    with pytest.raises(ValueError):
        manager.update_pipeline(
            stage="training",
            name="train_model",
            depends_on=["training.train_model"],
        )


def test_delete_pipeline_element(manager):
    manager.update_pipeline(
        stage="preprocessing",
        name="clean_data",
        path=Path("src/preprocess.py"),
    )
    manager._config.save()

    manager.delete_element("preprocessing", "clean_data")
    manager._config.save()

    assert manager._config.get(
        "pipeline.stages.preprocessing.elements.clean_data"
    ) is None


def test_prevent_delete_if_dependency_exists(manager):
    manager.update_pipeline(
        stage="preprocessing",
        name="clean_data",
        path=Path("src/preprocess.py"),
    )

    manager.update_pipeline(
        stage="training",
        name="train_model",
        path=Path("src/train.py"),
        depends_on=["preprocessing.clean_data"],
    )

    manager._config.save()

    with pytest.raises(ValueError):
        manager.delete_element("preprocessing", "clean_data")