import json
from pathlib import Path
import shutil
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from dist_automl.working_dir import WorkingDirectory,YamlManager



class ProjectDict(BaseModel):
    name: str
    root: Path
    deleted: bool = False
    metadata: Dict = Field(default_factory=dict)

    def __repr__(self):
        des =  f"""
        name: {self.name},
        directory: {str(self.root)}
        metadata: {self.metadata if self.metadata is None else "None"}
        """
        return des

class ProjectsConfig(BaseModel):
    projects: List[ProjectDict] = Field(default_factory=list)
    uv_path: Optional[Path] = None
    


#-----------------------------------------------------------


class ProjectJSON:

    def __init__(self,json_path:Path = None):
        if json_path is not None:
            self.path_to_json = json_path.resolve()
        else:
            self.path_to_json = (Path(__file__).parent / "all_projects.json").resolve()
        
        self.path_to_cwp = self.path_to_json.parent / "current_project.txt"
        self.path_to_cwd = self.path_to_json.parent / "current_project_root.txt"

        self.path_to_json.touch(exist_ok=True)

        if self.path_to_json.stat().st_size == 0:
            self.project_config = ProjectsConfig()
            self._save()
        else:
            self._load()
            
        if self.project_config.uv_path is None:
            uv_path = shutil.which("uv")
            self.project_config.uv_path = uv_path
            self._save()

    def _load(self):
        try:
            raw_data = json.loads(self.path_to_json.read_text())
            self.project_config = ProjectsConfig(**raw_data)
        except Exception:
            self.project_config = ProjectsConfig()
            self._save()

    def _save(self):
        try:
            self.path_to_json.write_text(
                json.dumps(
                    self.project_config.model_dump(mode="json"),
                    indent=4,
                    default=str
                )
            )
        except Exception as e:
            raise RuntimeError(f"Error writing project config: {e}")

    def _find_index(self, name: str) -> Optional[int]:
        for idx, project in enumerate(self.project_config.projects):
            if project.name == name:
                return idx
        return None

    def set_cwp(self,name):
        idx = self._find_index(name)
        
        if idx is not None:
            self.path_to_cwp.write_text(self.project_config.projects[idx].name)
            self.path_to_cwd.write_text(self.project_config.projects[idx].root.__str__())
        else: 
            raise ValueError(f"No project with name : {name}")
        
    def get_cwp(self):
        return self.path_to_cwp.read_text() if self.path_to_cwp.exists() else None
    
    def add_or_update(
        self,
        name: str,
        root: Path,
        metadata: Optional[Dict] = None,
        overwrite: bool = False
    ) -> None:

        idx = self._find_index(name)

        if idx is not None:
            if not overwrite and not self.project_config.projects[idx].deleted:
                raise ValueError(f"Project '{name}' already exists. Use overwrite=True.")
            
            self.project_config.projects[idx] = ProjectDict(
                name=name,
                root=root,
                deleted=False,
                metadata=metadata or {}
            )
        else:
            _ = WorkingDirectory(project_root=root)
            self.project_config.projects.append(
                ProjectDict(
                    name=name,
                    root=root,
                    deleted=False,
                    metadata=metadata or {}
                )
            )

        self._save()

    def delete(self, name: str) -> None:
        idx = self._find_index(name)

        if idx is None:
            raise ValueError(f"Project '{name}' not found.")

        self.project_config.projects[idx].deleted = True
        self._save()

    def retrack(self, name: str) -> None:
        idx = self._find_index(name)

        if idx is None:
            raise ValueError(f"Project '{name}' not found.")

        self.project_config.projects[idx].deleted = False
        self._save()

    def list_projects(self, include_deleted: bool = False) -> List[ProjectDict]:
        if include_deleted:
            return self.project_config.projects
        return [p for p in self.project_config.projects if not p.deleted]