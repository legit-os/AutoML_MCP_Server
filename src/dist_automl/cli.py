import typer
from pathlib import Path
from typing import Annotated

from dist_automl.managers.project_manager import ProjectJSON

app = typer.Typer(name="Auto ML Manager")

@app.command()
def init(path: Annotated[Path, typer.Argument(help="Directory to initialize and track",
                                              file_okay=False,dir_okay=True,writable=True,
                                              resolve_path=True)] = Path(".")):
    projects_config = ProjectJSON()
    
    projects_config.add_or_update(name=path.name)