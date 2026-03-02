import pytest
from pathlib import Path
from dist_automl.working_dir.yaml_class import YamlConfig,YamlManager

def test_complete_ml_project(tmp_path):
    config_path = tmp_path / "full_project.yaml"
    config = YamlConfig(config_path)
    manager = YamlManager(config)
    utils_files = [
        "helpers",
        "metrics",
        "data_loader",
        "logger",
        "validators",
    ]

    for u in utils_files:
        manager.update_utils(u, Path(f"utils/{u}.py"))


    manager.update_analysis(
        "summary",
        path=Path("analysis/summary.py"),
        output_type="table",
    )

    manager.update_analysis(
        "correlation",
        path=Path("analysis/correlation.py"),
        output_type="graph",
    )

    manager.update_analysis(
        "feature_stats",
        path=Path("analysis/feature_stats.py"),
        output_type="list",
    )


    manager.update_pipeline(
        stage="preprocessing",
        name="load_data",
        path=Path("src/load.py"),
        depends_on=["utils.data_loader"],
    )

    manager.update_pipeline(
        stage="preprocessing",
        name="clean_data",
        path=Path("src/clean.py"),
        depends_on=["preprocessing.load_data", "utils.helpers"],
    )

    manager.update_pipeline(
        stage="feature_engineering",
        name="create_features",
        path=Path("src/features.py"),
        depends_on=["preprocessing.clean_data"],
    )

    manager.update_pipeline(
        stage="training",
        name="train_model",
        path=Path("src/train.py"),
        depends_on=[
            "feature_engineering.create_features",
            "utils.metrics",
        ],
    )

    manager.update_pipeline(
        stage="evaluation",
        name="evaluate_model",
        path=Path("src/evaluate.py"),
        depends_on=["training.train_model"],
    )

    manager.update_pipeline(
        stage="serving",
        name="api_server",
        path=Path("src/serve.py"),
        depends_on=["training.train_model", "utils.logger"],
    )



    assert len(config.get("utils.files")) == 5

    assert len(config.get("analysis.files")) == 3

    stages = config.get("pipeline.stages")
    assert len(stages) == 5  

    deps = config.get(
        "pipeline.stages.training.elements.train_model.depends_on"
    )
    assert "feature_engineering.create_features" in deps
    assert "utils.metrics" in deps

    assert config.get(
        "pipeline.stages.serving.elements.api_server.path"
    ) == "src/serve.py"



    reloaded = YamlConfig(config_path)

    assert reloaded.get("utils.files.helpers.path") == "utils/helpers.py"
    assert reloaded.get(
        "pipeline.stages.preprocessing.elements.clean_data.path"
    ) == "src/clean.py"