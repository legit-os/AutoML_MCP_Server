import os
import shutil
import json
import webbrowser
from pathlib import Path
from typing import Annotated, Optional, List, Dict

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme

# Custom theme for the CLI
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "bold magenta",
})

console = Console(theme=custom_theme)


from dist_automl.managers.projects_manager import ProjectJSON
from dist_automl.working_dir import WorkingDirectory, YamlManager




def richprint(object, color="green", json_: bool = False):
    if json_:
        if isinstance(object, dict):
            content = json.dumps(object, indent=4)
        else:
            content = str(object)
        console.print_json(content)
    else:
        console.print(object, style=color)

def print_header():
    """Prints a branded header for the CLI."""
    console.print()
    header_text = Text("AutoML MCP Manager", style="bold blue")
    console.print(Panel(header_text, subtitle="[dim]End-to-End ML Pipeline Orchestrator[/dim]", expand=False, border_style="blue"))
    console.print()

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




@app.command(help="List all projects (-a argument will give the info of deleted projects also)")
def list(all: Annotated[bool, typer.Option("-a", "--all")] = False):
    global projects_config
    print_header()
    
    projects = projects_config.list_projects(include_deleted=all)
    
    if not projects:
        console.print("[warning]No projects found.[/warning]")
        return

    table = Table(title="AutoML Projects", border_style="blue", header_style="bold cyan")
    table.add_column("Status", justify="center")
    table.add_column("Name", style="highlight")
    table.add_column("Root Directory", style="info")
    table.add_column("Metadata", style="success")

    cwp = projects_config.get_cwp()

    for p in projects:
        status = "✅"
        if p.deleted:
            status = "❌ [dim](deleted)[/dim]"
        elif p.name == cwp:
            status = "⭐ [bold]ACTIVE[/bold]"
            
        metadata_str = ", ".join([f"{k}={v}" for k, v in p.metadata.items()]) if p.metadata else "[dim]None[/dim]"
        table.add_row(status, p.name, str(p.root), metadata_str)

    console.print(table)
    
    
@app.command(help="Find and see a specific project by name")
def show(name: Optional[str] = None):
    global projects_config
    print_header()
    
    if name is None:
        list()
        return

    project = None
    for p in projects_config.list_projects(include_deleted=True):
        if p.name == name:
            project = p
            break
            
    if project is None:
        console.print(f"[error]No project found with name:[/error] [highlight]{name}[/highlight]")
    else:
        metadata_table = Table(show_header=False, box=None)
        for k, v in project.metadata.items():
            metadata_table.add_row(f"[bold cyan]{k}:[/bold cyan]", str(v))
            
        content = Text.assemble(
            ("Project Name: ", "bold white"), (project.name, "highlight"), "\n",
            ("Root Path:    ", "bold white"), (str(project.root), "info"), "\n",
            ("Status:       ", "bold white"), ("Deleted" if project.deleted else "Active", "success" if not project.deleted else "error"), "\n",
            ("Metadata:     ", "bold white"), "\n" if project.metadata else "None"
        )
        
        panel = Panel(
            content,
            title=f"[bold cyan]Project Details[/bold cyan]",
            border_style="blue",
            expand=False
        )
        console.print(panel)
        if project.metadata:
            console.print(metadata_table, indent_guides=True)
            




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
    
    
    if (path in [p.root for p in projects_config.list_projects()]):
        if (project_name in [p.name for p in projects_config.list_projects()]):
            console.print(f"[warning]Warning:[/warning] Project already exists at [info]{path}[/info] with name: [highlight]{project_name}[/highlight].\n")
            
            if overwrite is False:
                conf = typer.confirm("Do you want to overwrite the project details?")
                if conf:
                        projects_config.add_or_update(name=project_name, root=path, metadata=metadata, overwrite=True)
                        projects_config.set_cwp(project_name)
                        console.print(f"[success]Project {project_name} details updated and set as active.[/success]")
                else :
                    raise typer.Exit(0)
            else:
                console.print("[info]Overwriting project details...[/info]")
                projects_config.add_or_update(name=project_name, root=path, metadata=metadata, overwrite=True)
                projects_config.set_cwp(project_name)
                console.print(f"[success]Project {project_name} details updated and set as active.[/success]")
        else:
            console.print("[error]Error:[/error] Name of a project can't be changed. All projects must have a unique name and location.", style="error")
    else:
        console.print("[info]Adding a new project...[/info]")
        projects_config.add_or_update(name=project_name, root=path, metadata=metadata)
        projects_config.set_cwp(project_name)
        console.print(f"[success]Success![/success] Project [highlight]{project_name}[/highlight] at [info]{str(path)}[/info] is now the active project.")
        
        
@app.command(help="Set a project to work on with mcp")
def set(name: Optional[str]):
    global projects_config
    
    if name is not None:
        if name not in [p.name for p in projects_config.list_projects()]:
            console.print(f"[error]Error:[/error] No project with name: [highlight]{name}[/highlight]")
        else:
            projects_config.set_cwp(name)
            console.print(f"Current working project is now: [success]{projects_config.get_cwp()}[/success]")

    else:
        if getcurrentProject() is not None:
            projects_config.set_cwp(getcurrentProject().name)
        else:
            raise typer.BadParameter("This command takes the parameter 'name' or it should run in a project registered through 'init' command")
        
@app.command(help="Get the current working project")
def get():
    global projects_config
    cwp = projects_config.get_cwp()
    if cwp:
        console.print(f"Current working project: [success]{cwp}[/success]")
    else:
        console.print("[warning]No project is currently set.[/warning]")
        
@app.command(help="Delete a project by Name")
def delete(name: Annotated[str,"Name of the Project that you want to delete"]):
    global projects_config
    
    if name not in [p.name for p in projects_config.list_projects()]:
        console.print(f"[error]Error:[/error] No projects with the name: [highlight]{name}[/highlight]")
    else:
        projects_config.delete(name=name)
        console.print(f"[success]Deleted project:[/success] [highlight]{name}[/highlight]")
        
        
# @app.command(help="Recover a deleted project (Only recovers the config file)")
# def recover(name: Annotated[str,"Name of the deleted project that needs to be recovered"]):
#     global projects_config
#     if name not in [p.name for p in projects_config.list_projects(True) if p.deleted]:
#         typer.echo(f"No deleted projects found with name : {name}")
#     else:
#         projects_config.retrack(name)
        
    


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
            mn.update_dataset(name=name, source=source,
                             dtype=dtype, description=description,
                             metadata=metadata)
        console.print(f"[success]Successfully added/updated dataset:[/success] [highlight]{name}[/highlight]")
    else:
        console.print("[error]Error:[/error] No current working project found. Use [info]'automl set'[/info] to set a project.", style="error")
    


@app.command(help="Launch the custom React/FastAPI dashboard")
def dashboard(
    host: str = "127.0.0.1",
    port: int = 8000,
):
    import uvicorn
    from dist_automl.dashboard_maker_custom.server import app as dashboard_app, static_dir
    
    url = f"http://{host}:{port}"
    richprint(f"Loading frontend from: {static_dir}", color="yellow")
    if not static_dir.exists():
        richprint("Warning: Frontend build not found! Dashboard may show a blank page.", color="red")
        richprint("Run 'npm run build' in the frontend directory first.", color="yellow")
        
    richprint(f"Launching dashboard at {url}", color="cyan")
    
    # Open browser in a separate thread/process
    import threading
    def open_browser():
        import time
        time.sleep(2.0) # Give the server a moment to start
        webbrowser.open(url)
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run(dashboard_app, host=host, port=port)

def find_root(package_name="src"):
    current_path = Path(__file__)
    root_path = None
    print(current_path.parents)
    for parent in [current_path] + list(current_path.parents):
        if parent.name == package_name:
            root_path = parent
            break
            
    if not root_path:
        root_path = current_path.parent
    
    return str(root_path)
    
@app.command()
def mcp():
    tool_root = Path(__file__).parent.parent.parent.parent
    server_path = Path(__file__).parent / "mcp_server.py"
    uv_path = shutil.which("uv")
    
    schema = {
        "mcpServers": {
            "Auto_ML": {
                "command": f"{uv_path}",
                "args": ["--directory",
                         f"{tool_root}",
                         "run",
                         f"{server_path}"]
            }
        }
    }
    
    print_header()
    console.print(Panel("[bold cyan]MCP Server Configuration[/bold cyan]\nCopy the following JSON into your MCP settings file.", border_style="blue"))
    
    schema_json = json.dumps(schema, indent=4)
    syntax = Syntax(schema_json, "json", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    console.print("\n[dim]Tip: You can use this configuration in Claude Desktop or other MCP-compatible clients.[/dim]")
    

if __name__ == "__main__":
    app()
        
        
