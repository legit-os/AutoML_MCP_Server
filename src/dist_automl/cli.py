import os
import subprocess
import sys

import typer
from pathlib import Path
from typing import Annotated, Optional,List,Dict


from dist_automl.managers.projects_manager import ProjectJSON
from dist_automl.working_dir import WorkingDirectory, YamlManager
from dist_automl.dashboard_maker.server import app as flaskapp




projects_config = ProjectJSON()

app = typer.Typer(name="Auto ML Manager")

def getcurrentProject():
    global projects_config
    
    cwd = Path(os.getcwd())
    projects = [p for p in projects_config.list_projects() if p.root.as_posix() == cwd.as_posix()]
    
    if len(projects) == 0:
        return None
    
    projects_config.set_cwp(projects[0].name)
    
    return projects[0]

def parse_key_value(settings: List[str]) -> Dict[str, str]:
    items = {}
    for item in settings:
        try:
            key, value = item.split("=", 1)
            items[key] = value
        except ValueError:
            typer.echo(f"Warning: Skipping invalid pair '{item}' (must be key=value)")
    return items




@app.command(help="List all projects")
def list(all : Annotated[bool,typer.Option("-a","--all")] = False):
    global projects_config
    
    if not all:
        typer.echo([p for p in projects_config.list_projects()])
    else :
        typer.echo(projects_config.list_projects(True))
    
    
@app.command(help="Find and see a specific project by name")
def show(name: Optional[str] = None):
    global projects_config
    if name is None:
        typer.echo(projects_config.list_projects())
    else :
        project = [p for p in projects_config.list_projects() if p.name == name] 
        if len(project) == 0:
            typer.echo(f"No projects found for the name : {name}")
        else :
            typer.echo(project) 




@app.command(help=
             """
             Initialize a directory for Auto ML to track.
             Along with Path and Name, you can provide other metadata objects with "--meta key=value" for the project
             If the project already exists it will be be updated if overwrite argument is True
             """)
def init(path: Annotated[Path, typer.Argument(help="Directory to initialize and track",
                                              file_okay=False,dir_okay=True,writable=True,
                                              )] = Path("."),
         name : Optional[Annotated[str,"Name of the project"]] = None,
         overwrite : Annotated[bool, typer.Option("--overwrite", "-o")] = False,
         metadata: Annotated[Optional[List[str]], typer.Option("--meta","-m", help="Key-value pairs like -m k=v")] = None
         ):
    global projects_config    
    path = path.resolve()
    project_name = path.name if name is None else name
    
    metadata = parse_key_value(metadata or [])
    
    
    if  (path in [p.root for p in projects_config.list_projects()]):
        if (project_name in [p.name for p in projects_config.list_projects()]):
            typer.echo(path,project_name)
            
        
            typer.echo(f"Warning: Project already exists at {path} with name: {project_name}.\n")
            
            if overwrite is False:
                conf = typer.confirm("Do you want to overwrite on the project details")
                if conf:
                        projects_config.add_or_update(name=project_name, root=path,metadata=metadata,overwrite=True)
                        projects_config.set_cwp(project_name)
                else :
                    typer.Exit(0)
            else:
                typer.echo("Overwritting the project details")
                projects_config.add_or_update(name=project_name, root=path,metadata=metadata,overwrite=True)
                projects_config.set_cwp(project_name)
        else:
            typer.echo("Name of a project can't be changed. All projects have unique name and location")
    else:
        projects_config.add_or_update(name=project_name, root=path,metadata=metadata)
        projects_config.set_cwp(project_name)
        
        
@app.command(help="Set a project to work on with mcp")
def set(name: Optional[str]):
    global projects_config
    
    if name is not None:
        if name not in [p.name for p in projects_config.list_projects()]:
            typer.echo(f"No projects with name : {name}")
        else:
            projects_config.set_cwp(name)
            typer.echo(f"Current working project is {projects_config.get_cwp()}")

    else:
        if getcurrentProject() is not None:
            projects_config.set_cwp(getcurrentProject().name)
        else:
            raise typer.BadParameter("This command takes the parameter 'name' or it should run in a project registered through 'init' command")
        
@app.command(help="Get the current working project")
def get():
    global projects_config
    typer.echo(projects_config.get_cwp() or "No Projects\n")
        
@app.command(help="Delete a project by Name")
def delete(name: Annotated[str,"Name of the Project that you want to delete"]):
    global projects_config
    
    if name not in [p.name for p in projects_config.list_projects()]:
        typer.echo(f"No projects with the name : {name}")
    else:
        projects_config.delete(name=name)
        
        
@app.command(help="Recover a deleted project (Only recovers the config file)")
def recover(name: Annotated[str,"Name of the deleted project that needs to be recovered"]):
    global projects_config
    if name not in [p.name for p in projects_config.list_projects(True) if p.deleted]:
        typer.echo(f"No deleted projects found with name : {name}")
    else:
        projects_config.retrack(name)
        
    


def validate_source(value: str):
    path_attempt = Path(value)
    
    if path_attempt.exists():
        return path_attempt.resolve()
    
    return value

@app.command(help="Add a dataset to the project config")
def data(
    source: Annotated[str, typer.Argument(callback=validate_source, help="A path or name string")],
    name : Annotated[str,typer.Option("--name","-n")],
    dtype: Annotated[str, typer.Option("--type","-t")] = None,
    description : Annotated[str, typer.Option("-d","--des")] = None,
    metadata: Annotated[Optional[List[str]], typer.Option("--meta","-m", help="Key-value pairs like -m k=v")] = None
    
):
    global projects_config
    
    metadata = parse_key_value(metadata or [])
    
    pr = getcurrentProject()
    print(pr)
    if pr is not None:
        wd = WorkingDirectory(pr.root)
        mn = wd._manager
        with mn:
            mn.update_dataset(name=name,source=source,
                                    dtype=dtype,description=description,
                                    metadata=metadata)
    else:
        typer.echo("No current working projects found, Use 'set' command to set a project as working project")   
    


@app.command()
def dashboard(
    host: str = "127.0.0.1",
    port: int = 5000,
):
    flaskapp.run(
        host=host,
        port=port,
        debug=True
    )

if __name__ == "__main__":
    app()
        
        
