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
    
    
    
    
#--------------------------------------------------------------------------------



    def _validate_relative_path(self, path: Path, expected_root: str) -> Path:
        if not isinstance(path, Path):
            raise TypeError("path must be a pathlib.Path")

        path = path.expanduser()

        if path.is_absolute():
            try:
                relative_path = path.resolve().relative_to(self._root.resolve())
            except ValueError:
                raise ValueError("Absolute path must be inside project root")
        else:
            relative_path = path
            
        if ".." in relative_path.parts:
            raise ValueError("Path traversal outside project root is not allowed")

        if relative_path.suffix != ".py":
            raise ValueError("Only .py files are allowed")

        parts = relative_path.parts
        
        if not parts or parts[0] != expected_root:
            raise ValueError(f"Path must start with '{expected_root}/'")

        return relative_path
    
    
    def _absolute(self, relative_path: Path) -> Path:
        return (self._root / relative_path).resolve()

    def _create_file_if_needed(
        self,
        relative_path: Path,
        content: str = "",
        overwrite: bool = True,
    ) -> None:
        abs_path = self._absolute(relative_path)

        abs_path.parent.mkdir(parents=True, exist_ok=True)

        if abs_path.exists() and not overwrite:
            return

        abs_path.write_text(content, encoding="utf-8")


    def _delete_file_if_exists(self, relative_path: Path) -> None:
        abs_path = self._absolute(relative_path)
        if abs_path.exists():
            abs_path.unlink()
            
#-----------------------------------------------------------------

    def update_utils(
        self,
        name: str,
        path: Path,
        metadata: Optional[dict] = None,
        content: str = "",
        overwrite: bool = True,
    ) -> None:
        relative_path = self._validate_relative_path(path, "utils")

        try:
            with self._manager:
                self._create_file_if_needed(
                    relative_path,
                    content=content,
                    overwrite=overwrite,
                )

                self._manager.update_utils(
                    name=name,
                    path=relative_path,
                    metadata=metadata,
                )

        except Exception:
            self._delete_file_if_exists(relative_path)
            raise
            
            
            
    def delete_utils(self, name: str) -> None:
        entry = self._config.get(f"utils.files.{name}")
        if not entry:
            raise KeyError(f"Utils entry '{name}' not found")

        relative_path = Path(entry["path"])

        with self._manager:
            self._manager.delete_utils(name)
            self._delete_file_if_exists(relative_path)
            
            
#--------------------------------------------------------------------


    def update_analysis(
        self,
        name: str,
        path: Path,
        output_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        content: str = "",
        overwrite: bool = True,
    ) -> None:
        relative_path = self._validate_relative_path(path, "analysis")

        try:
            with self._manager:
                self._create_file_if_needed(
                    relative_path,
                    content=content,
                    overwrite=overwrite,
                )

                self._manager.update_analysis(
                    name=name,
                    path=relative_path,
                    output_type=output_type,
                    metadata=metadata,
                )

        except Exception:
            self._delete_file_if_exists(relative_path)
            raise
            
            
    def delete_analysis(self, name: str) -> None:
        entry = self._config.get(f"analysis.files.{name}")
        if not entry:
            raise KeyError(f"Analysis entry '{name}' not found")

        relative_path = Path(entry["path"])

        with self._manager:
            self._manager.delete_analysis(name)
            self._delete_file_if_exists(relative_path)
            
            
#----------------------------------------------------------------

    def update_pipeline_element(
        self,
        stage: str,
        name: str,
        path: Path,
        metadata: Optional[dict] = None,
        depends_on: Optional[list[str]] = None,
        content: str = "",
        overwrite: bool = True,
    ) -> None:
        

        relative_path = self._validate_relative_path(path, "pipeline")

        try:
            with self._manager:
                self._create_file_if_needed(
                    relative_path,
                    content=content,
                    overwrite=overwrite,
                )

                self._manager.update_pipeline(
                    stage=stage,
                    name=name,
                    path=relative_path,
                    metadata=metadata,
                    depends_on=depends_on,
                )

        except Exception:
            self._delete_file_if_exists(relative_path)
            raise
            
    def delete_pipeline_element(self, stage: str, name: str) -> None:

        entry = self._config.get(f"pipeline.stages.{stage}.elements.{name}")
        if not entry:
            raise KeyError(f"Pipeline element '{stage}.{name}' not found")

        relative_path = Path(entry["path"])

        with self._manager:
            self._manager.delete_element(stage, name)
            self._delete_file_if_exists(relative_path)
            
    def check_sync(self) -> list[str]:
        return self._manager.check_project_sync(self._root)
    
    
    
if __name__ == "__main__":
    test_path = Path(__file__).parent.parent.parent.parent.absolute() / "wd_test"
    
    Dir = WorkingDirectory(test_path)
    
    Dir.check_sync()
    Dir.update_utils("helper",Path("utils/helper.py"),content="works")
    Dir.update_analysis("bar graph",Path("analysis/barg.py"),"graph",content="worksss")
    Dir.update_pipeline_element("prepro_2","colmix",Path("pipeline/ok.py"),content="work")
    Dir.check_sync()
    _ = input()
    Dir.delete_utils("helper")
    Dir.delete_analysis("bar graph")
    Dir.delete_pipeline_element(stage="prepro",name="colmix")
    # Dir.delete_pipeline_element(stage="prepro")
    Dir.check_sync()
    
    