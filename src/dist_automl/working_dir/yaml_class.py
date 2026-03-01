from pathlib import Path
from enum import Enum
from typing import Any, Callable, List, Union, Optional, Type, Dict
from pydantic import BaseModel, Field, model_validator,ValidationError
import yaml
from filelock import FileLock
import copy


YamlDType = Union[str, int, float, bool, None, list, dict]


class AnalysisOutputType(str, Enum):
    table = "table"
    graph = "graph"
    list = "list"
    float = "float"
    

class ExecuteType(str, Enum):
    function = "function"
    class_method = "class_method"
    
    
    
    
    
    
class InputSource(str, Enum):
    file = "file"
    unit_output = "unit_output"
    literal = "literal"
    config = "config"
    env = "env"




class AnalysisFile(BaseModel):
    path: Path
    output_type: AnalysisOutputType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class UtilsFile(BaseModel):
    path: Path
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    
    
    
    
class InputDefinition(BaseModel):
    type: str
    source: InputSource

    value: Optional[Any] = None

    reference: Optional[str] = None

    @model_validator(mode="after")
    def validate_input(self):
        if self.source in [InputSource.file, InputSource.literal]:
            if self.value is None:
                raise ValueError("Input with source 'file' or 'literal' must define 'value'.")

        if self.source == InputSource.unit_output:
            if self.reference is None:
                raise ValueError("Input with source 'unit_output' must define 'reference'.")

        return self

class OutputDefinition(BaseModel):
    type: str
    persist: bool = False
    save_as: Optional[Path] = None

    @model_validator(mode="after")
    def validate_output(self):
        if self.persist and self.save_as is None:
            raise ValueError("Persisted outputs must define 'save_as'.")
        return self
    
    


class ExecuteDefinition(BaseModel):
    type: ExecuteType
    symbol: Optional[str] = None
    class_name: Optional[str] = None
    method: Optional[str] = None

    @model_validator(mode="after")
    def validate_execute(self):
        if self.type == ExecuteType.function:
            if not self.symbol:
                raise ValueError("Function execution requires 'symbol'.")

        if self.type == ExecuteType.class_method:
            if not self.class_name or not self.method:
                raise ValueError("Class method execution requires 'class_name' and 'method'.")

        return self





class PipelineUnit(BaseModel):
    path: Path

    execute: ExecuteDefinition

    inputs: Dict[str, InputDefinition] = Field(default_factory=dict)
    outputs: Dict[str, OutputDefinition] = Field(default_factory=dict)

    depends_on: List[str] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)





class PipelineConfig(BaseModel):
    units: Dict[str, PipelineUnit]

class AnalysisConfig(BaseModel):
    path: Path
    files: Dict[str, AnalysisFile]

class UtilsConfig(BaseModel):
    path: Path
    files: Dict[str, UtilsFile]




#-------------------------------------
class ProjectManifest(BaseModel):
    analysis: AnalysisConfig
    utils: UtilsConfig
    pipeline: PipelineConfig
    
#------------------------------------

class YamlConfig():
    def __init__(self, path: Path, schema: Optional[Type[BaseModel]] = None):
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
        self._transaction_backup = copy.deepcopy(self._data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_transaction = False

        if exc_type is not None:
            self._data = self._transaction_backup
            self._dirty = False
            self._changes.clear()
            return False

    def __repr__(self):
        return (
            f"YamlConfig(path='{self._path}', "
            f"keys={list(self._data.keys())}, "
            f"dirty={self._dirty})"
        )

    def __str__(self):
        return yaml.safe_dump(self._data, sort_keys=False)
