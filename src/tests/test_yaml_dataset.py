import pytest
from pathlib import Path
from dist_automl.working_dir import YamlConfig,YamlManager



def test_update_dataset_basic(tmp_path):
    manager = YamlManager(YamlConfig(tmp_path))
    manager.update_dataset(
        name="raw_sales",
        source=Path("data/raw/sales.csv"),
        dtype="csv",
        description="raw",
        metadata={"source": "internal"},
    )

    manager._config.save()

    assert manager._config.get(
        "datasets.files.raw_sales.source"
    ) == "data/raw/sales.csv"

    assert manager._config.get(
        "datasets.files.raw_sales.type"
    ) == "csv"

    assert manager._config.get(
        "datasets.files.raw_sales.description"
    ) == "raw"

    assert manager._config.get(
        "datasets.files.raw_sales.metadata.source"
    ) == "internal"
    
def test_update_dataset_partial_update(tmp_path):
    manager = YamlManager(YamlConfig(tmp_path))
    manager.update_dataset(
        name="raw_sales",
        source=Path("data/raw/sales.csv"),
        dtype="csv",
    )

    manager.update_dataset(
        name="raw_sales",
        source="sqlite",
        description="raw",
    )

    manager._config.save()

    assert manager._config.get(
        "datasets.files.raw_sales.source"
    ) == "sqlite"

    assert manager._config.get(
        "datasets.files.raw_sales.type"
    ) == "csv"

    assert manager._config.get(
        "datasets.files.raw_sales.description"
    ) == "raw"