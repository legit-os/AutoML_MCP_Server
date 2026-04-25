from pathlib import Path
from enum import Enum
from typing import Any, Literal, Union, Optional, Type, Dict, List
from pydantic import BaseModel, Field, model_validator, ValidationError
import yaml
from filelock import FileLock
import copy


YamlDType = Union[str, int, float, bool, None, list, dict]


class AnalysisFile(BaseModel):
    path: Optional[Path] = None
    output_type: Optional[Literal["table", "graph", "list", "float"]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalysisConfig(BaseModel):
    path: Optional[Path] = None
    files: Optional[Dict[str, AnalysisFile]] = Field(default_factory=dict)





class UtilsFile(BaseModel):
    path: Optional[Path] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UtilsConfig(BaseModel):
    path: Optional[Path] = None
    files: Optional[Dict[str, UtilsFile]] = Field(default_factory=dict)






class PipelineElement(BaseModel):
    path: Optional[Path] = None

    depends_on: Optional[List[str]] = Field(default_factory=list)

    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PipelineStage(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    elements: Optional[Dict[str, PipelineElement]] = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    stages: Optional[Dict[str, PipelineStage]] = Field(default_factory=dict)


class DatasetFile(BaseModel):
    path: Optional[Path] = None
    type: Optional[str] = None
    role: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DatasetConfig(BaseModel):
    path: Optional[Path] = None
    files: Optional[Dict[str, DatasetFile]] = Field(default_factory=dict)

# -------------------------------------
class ProjectManifest(BaseModel):
    analysis: Optional[AnalysisConfig] = None
    utils: Optional[UtilsConfig] = None
    pipeline: Optional[PipelineConfig] = None
    datasets: Optional[DatasetConfig] = None


# ------------------------------------




class YamlConfig:
    def __init__(self, path: Path, schema: Optional[Type[BaseModel]] = ProjectManifest):
        if not isinstance(path, Path):
            raise TypeError("path must be pathlib.Path object, even str not allowed")

        self._path = path

        if self._path.is_dir():
            self._path = self._path / "config.yaml"

        if self._path.suffix not in [".yaml", ".yml"]:
            raise ValueError(
                f"is this {self._path.suffix} the extention for yaml files?"
            )

        self._schema = schema
        self._lock = FileLock(str(self._path) + ".lock")

        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text("")

        self._data = self._load()
        self._original_data = copy.deepcopy(self._data)

        self._dirty = False
        self._changes = []
        self._in_transaction = False

    def _load(self) -> dict:
        with self._lock:
            with self._path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}

    def _validate(self):
        if self._schema:
            try:
                self._schema(**self._data)
            except ValidationError as e:
                raise ValueError(f"Schema validation failed:\n{e}")

    def _set_nested(self, key: str, value: YamlDType):
        keys = key.split(".")
        ref = self._data

        for k in keys[:-1]:
            if k not in ref or not isinstance(ref[k], dict):
                ref[k] = {}
            ref = ref[k]

        old_value = ref.get(keys[-1], None)
        ref[keys[-1]] = value

        self._dirty = True
        self._changes.append({"key": key, "old": old_value, "new": value})

    def _get_nested(self, key: str, default=None):
        keys = key.split(".")
        ref = self._data

        for k in keys:
            if not isinstance(ref, dict) or k not in ref:
                return default
            ref = ref[k]

        return ref

    def update(self, key: str, value: YamlDType):
        self._set_nested(key, value)

    def get(self, key: str, default=None):
        return self._get_nested(key, default)

    def delete(self, key: str):
        keys = key.split(".")
        ref = self._data

        for k in keys[:-1]:
            if k not in ref:
                return
            ref = ref[k]

        if keys[-1] in ref:
            old = ref[keys[-1]]
            del ref[keys[-1]]
            self._dirty = True
            self._changes.append({"key": key, "old": old, "new": None})
            

    def save(self):
        if not self._dirty:
            return

        self._validate()

        with self._lock:
            with self._path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(self._data, f, sort_keys=False, default_flow_style=False)

        self._original_data = copy.deepcopy(self._data)
        self._dirty = False
        self._changes.clear()

    def rollback(self):
        self._data = copy.deepcopy(self._original_data)
        self._dirty = False
        self._changes.clear()

    def changes(self):
        return self._changes.copy()

    def __enter__(self):
        self._in_transaction = True
        # self._transaction_backup = copy.deepcopy(self._data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_transaction = False

        if exc_type is not None:
            self.rollback()
            return False
        else:
            self.save()

    def __repr__(self):
        return (
            f"YamlConfig(path='{self._path}', "
            f"keys={list(self._data.keys())}, "
            f"dirty={self._dirty})"
        )

    def __str__(self):
        return yaml.safe_dump(self._data, sort_keys=False)




#--------------------------------------------------------------------


class YamlManager():
    def __init__(self,config : YamlConfig):
        self._config = config
    
    
    def update_utils(
        self,
        name: str,
        path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
            cfg = self._config

        
            if cfg.get("utils") is None:
                cfg.update("utils", {})

            if cfg.get("utils.files") is None:
                cfg.update("utils.files", {})

            if path is not None:
                cfg.update(f"utils.files.{name}.path", path.as_posix())

            if metadata is not None:
                cfg.update(f"utils.files.{name}.metadata", metadata)
                
    def delete_utils(self, name: str):
            cfg = self._config
        
            cfg.delete(f"utils.files.{name}")
            
    
    
    


    def update_analysis(
        self,
        name: str,
        path: Optional[Path] = None,
        output_type: Optional[Literal["table", "graph", "list", "float"]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
            cfg = self._config

        
            if cfg.get("analysis") is None:
                cfg.update("analysis", {})

            if cfg.get("analysis.files") is None:
                cfg.update("analysis.files", {})

            if path is not None:
                cfg.update(f"analysis.files.{name}.path", path.as_posix())

            if output_type is not None:
                cfg.update(f"analysis.files.{name}.output_type", output_type)

            if metadata is not None:
                cfg.update(f"analysis.files.{name}.metadata", metadata)
                
    def delete_analysis(self, name: str):
            cfg = self._config
        
            cfg.delete(f"analysis.files.{name}")
            



    def update_pipeline(
        self,
        stage: str,
        name: str,
        path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
    ):

            cfg = self._config

            if cfg.get("pipeline") is None:
                cfg.update("pipeline", {})

            if cfg.get("pipeline.stages") is None:
                cfg.update("pipeline.stages", {})

            if cfg.get(f"pipeline.stages.{stage}") is None:
                cfg.update(f"pipeline.stages.{stage}", {})

            if cfg.get(f"pipeline.stages.{stage}.elements") is None:
                cfg.update(f"pipeline.stages.{stage}.elements", {})


            if depends_on:
                for dep in depends_on:
                    if not isinstance(dep, str):
                        raise ValueError(f"Invalid dependency format: {dep}. \n Dependency '{dep}' must be in format 'stage.element' or 'utils.file'")

                    if "." not in dep:
                        raise ValueError(
                            f"Dependency '{dep}' must be in format 'stage.element' or 'utils.file'"
                        )

                    dep_stage, dep_name = dep.split(".", 1)

                    if dep_stage == stage and dep_name == name:
                        raise ValueError("Element cannot depend on itself.")

                    if dep_stage == "utils":
                        if cfg.get(f"utils.files.{dep_name}") is None:
                            raise ValueError(
                                f"Dependency '{dep}' does not exist in utils."
                            )

                    else:
                        if cfg.get(f"pipeline.stages.{dep_stage}") is None:
                            raise ValueError(
                                f"Dependency stage '{dep_stage}' does not exist."
                            )
                        if (
                            cfg.get(
                                f"pipeline.stages.{dep_stage}.elements.{dep_name}"
                            )
                            is None
                        ):
                            raise ValueError(
                                f"Dependency element '{dep}' does not exist."
                            )


            element_base = f"pipeline.stages.{stage}.elements.{name}"

            if path is not None:
                cfg.update(f"{element_base}.path", path.as_posix())

            if metadata is not None:
                cfg.update(f"{element_base}.metadata", metadata)

            if depends_on is not None:
                cfg.update(f"{element_base}.depends_on", depends_on)
                
    def delete_element(self, stage: str, name: str):
            cfg = self._config

            element_key = f"pipeline.stages.{stage}.elements.{name}"
            if cfg.get(element_key) is None:
                raise ValueError(f"Element '{stage}.{name}' does not exist.")

            target_full_name = f"{stage}.{name}"

            stages = cfg.get("pipeline.stages", {})

            for s_name, stage_data in stages.items():

                elements = stage_data.get("elements", {})

                for e_name, element_data in elements.items():

                    depends = element_data.get("depends_on", [])

                    if target_full_name in depends:
                        raise ValueError(
                            f"Cannot delete '{target_full_name}'. "
                            f"It is required by '{s_name}.{e_name}'."
                        )

            cfg.delete(element_key)
    


    def update_dataset(
        self,
        name: str,
        source: str,
        dtype: Optional[str] = None,
        description : Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

            cfg = self._config

            if cfg.get("datasets") is None:
                cfg.update("datasets", {})

            if cfg.get("datasets.files") is None:
                cfg.update("datasets.files", {})

            base_key = f"datasets.files.{name}"

            if source is not None:
                cfg.update(f"{base_key}.source", source.as_posix() if isinstance(source,Path) else source)

            if dtype is not None:
                cfg.update(f"{base_key}.type", dtype)

            if description is not None:
                cfg.update(f"{base_key}.description", description)

            if metadata is not None:
                cfg.update(f"{base_key}.metadata", metadata)
    
    
    def delete_dataset(self, name: str):
        cfg = self._config

        dataset_key = f"datasets.files.{name}"
        if cfg.get(dataset_key) is None:
            raise ValueError(f"Dataset '{name}' does not exist.")

        cfg.delete(dataset_key)


    def __enter__(self):
        self._config._in_transaction = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._config._in_transaction = False

        if exc_type is not None:
            self._config.rollback()
            return False
        else:
            self._config.save()

    def __repr__(self):
        return (
            f"YamlConfig(path='{self._config._path}', "
            f"keys={list(self._config._data.keys())}, "
            f"dirty={self._config._dirty})"
        )

    def __str__(self):
        return yaml.safe_dump(self._config._data, sort_keys=False)
    


    def check_project_sync(self, project_root: Path) -> List[str]:
        config = self._config

        warnings = []

        if not isinstance(project_root, Path):
            warnings.append("Project root is not a valid Path object.")
            return warnings

        if not project_root.exists():
            warnings.append(f"Project root does not exist: {project_root}")
            return warnings

        def resolve_path(p: str) -> Path:
            path_obj = Path(p)
            if path_obj.is_absolute():
                return path_obj
            return project_root / path_obj

        utils_files = config.get("utils.files", {}) or {}

        for name, data in utils_files.items():
            file_path = data.get("path")

            if not file_path:
                warnings.append(f"Utils '{name}' has no path defined.")
                continue

            resolved = resolve_path(file_path)

            if not resolved.exists():
                warnings.append(f"Utils file missing: {resolved}")

        analysis_files = config.get("analysis.files", {}) or {}

        for name, data in analysis_files.items():
            file_path = data.get("path")

            if not file_path:
                warnings.append(f"Analysis '{name}' has no path defined.")
                continue

            resolved = resolve_path(file_path)

            if not resolved.exists():
                warnings.append(f"Analysis file missing: {resolved}")

        stages = config.get("pipeline.stages", {}) or {}

        for stage_name, stage_data in stages.items():
            elements = stage_data.get("elements", {}) or {}

            for element_name, element_data in elements.items():

                file_path = element_data.get("path")

                if not file_path:
                    warnings.append(
                        f"Pipeline element '{stage_name}.{element_name}' has no path defined."
                    )
                    continue

                resolved = resolve_path(file_path)

                if not resolved.exists():
                    warnings.append(
                        f"Pipeline file missing: {resolved} "
                        f"(declared in {stage_name}.{element_name})"
                    )

        return warnings