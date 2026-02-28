from pathlib import Path
from typing import Optional
from dist_automl.working_dir.yaml_class import YamlConfig

directories = ["data_analysis", "feature_engineering", "model_trainer", "serving"]


class WorkingDirectory:
    def __init__(
        self, path: Path, config_file_name: Path | None, exist_ok: bool = False
    ) -> None:
        if not isinstance(path, Path):
            raise TypeError("path must be pathlib.Path object")

        if not isinstance(config_file_name, Path):
            raise TypeError("config_path must be pathlib.Path object")

        if not isinstance(exist_ok, bool):
            raise TypeError(
                "exist_ok must be a boolean, it is the same parameter that mkdir method takes"
            )

        if not path.is_absolute():
            raise ValueError("expected absolute path")

        self._path: Path = path
        self._config_path: Path = self._path / config_file_name.name

        if not self._path.is_dir():
            raise NotADirectoryError(f"Provided path is not a directory: {self._path}")
        self._path.mkdir(parents=True, exist_ok=exist_ok)

        self._config = YamlConfig(self._config_path)

    def create_file(self, relative_path: Path, content: Optional[str] = None) -> Path:
        pass

    def run_file(self, relative_path: Path) -> None:
        pass

    def delete_file(self, relative_path: Path) -> None:
        pass

    def list_files(self) -> list[Path]:
        pass

    def get_config(self):
        pass

    def update_config(self):
        pass
