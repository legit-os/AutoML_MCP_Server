from pathlib import Path
from typing import Optional

from dist_automl.working_dir.yaml_class import YamlConfig, YamlManager


class WorkingDirectory:
    BASE_FOLDERS = ("analysis", "utils", "pipeline")

    def __init__(
        self,
        project_root: Path,
        config_path: Optional[Path] = None,
        exist_ok: bool = True,
    ):
        if not isinstance(project_root, Path):
            raise TypeError("project_root must be a pathlib.Path")

        project_root = project_root.expanduser().resolve()

        if not project_root.is_absolute():
            raise ValueError("project_root must be an absolute path")




        self._root = project_root
        self._root.mkdir(parents=True, exist_ok=exist_ok)

        self._ensure_base_structure()





        if config_path is None:
            config_path = self._root / "config.yaml"
        else:
            if not isinstance(config_path, Path):
                raise TypeError("config_path must be a pathlib.Path")

            if not config_path.is_absolute():
                config_path = self._root / config_path

            config_path = config_path.resolve()

        if config_path.suffix not in (".yaml", ".yml"):
            raise ValueError("Config file must have .yaml or .yml extension")

        self._config_path = config_path

        self._config = YamlConfig(self._config_path)

        self._manager = YamlManager(self._config)



    def _ensure_base_structure(self) -> None:
        for folder in self.BASE_FOLDERS:
            (self._root / folder).mkdir(parents=True, exist_ok=True)




    @property
    def root(self) -> Path:
        return self._root

    @property
    def config(self) -> YamlConfig:
        return self._config

    @property
    def manager(self) -> YamlManager:
        return self._manager
    
    
    
