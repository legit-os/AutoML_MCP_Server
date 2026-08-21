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
    console.print(Panel(header_text, subtitle="[dim]ML Pipeline Orchestrator[/dim]", expand=True, border_style="blue"))
    console.print()

projects_config = ProjectJSON()

app = typer.Typer(name="Auto ML Manager")

def getcurrentProject():
    global projects_config
    
    cwd = Path(os.getcwd())
    projects = [p for p in projects_config.list_projects() if p.root.as_posix() == cwd.as_posix()]
    
    if len(projects) > 0:
        projects_config.set_cwp(projects[0].name)
        return projects[0]
    
    cwp_name = projects_config.get_cwp()
    if cwp_name is not None:
        for p in projects_config.list_projects():
            if p.name == cwp_name:
                return p
    
    return None

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
def list():
    global projects_config
    print_header()
    
    projects = projects_config.list_projects()
    
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
        if p.name == cwp:
            status = "⭐ [bold]ACTIVE[/bold]"
            
        metadata_str = ", ".join([f"{k}={v}" for k, v in p.metadata.items()]) if p.metadata else "[dim]None[/dim]"
        table.add_row(status, p.name, str(p.root), metadata_str)

    console.print(table)
    


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
        
    


def validate_source(value: str):
    path_attempt = Path(value)
    
    if path_attempt.exists():
        return path_attempt.resolve()
    
    return value

@app.command(help="Add or update a dataset in the project configuration", name="dataset")
def dataset(
    source: Annotated[str, typer.Argument(callback=validate_source, help="A path or name string")],
    name : Annotated[str,typer.Option("--name","-n", help="Unique name for the dataset")],
    dtype: Annotated[Optional[str], typer.Option("--type","-t", help="Type of dataset (csv, parquet, etc.)")] = None,
    description : Annotated[Optional[str], typer.Option("-d","--des", help="Brief description of the dataset")] = None,
    metadata: Annotated[Optional[List[str]], typer.Option("--meta","-m", help="Key-value pairs like -m k=v")] = None
    
):
    global projects_config
    
    metadata = parse_key_value(metadata or [])
    
    pr = getcurrentProject()
    if pr is not None:
        wd = WorkingDirectory(pr.root)
        wd.update_dataset(name=name, source=source,
                         dtype=dtype, description=description,
                         metadata=metadata)
        console.print(f"[success]Successfully added/updated dataset:[/success] [highlight]{name}[/highlight]")
    else:
        console.print("[error]Error:[/error] No current working project found. Use [info]'automl set'[/info] to set a project.", style="error")

@app.command(help="Delete a dataset from the project configuration", name="dataset-delete")
def dataset_delete(
    name: Annotated[str, typer.Argument(help="Name of the dataset to delete")]
):
    global projects_config
    
    pr = getcurrentProject()
    if pr is not None:
        wd = WorkingDirectory(pr.root)
        wd.delete_dataset(name=name)
        console.print(f"[success]Successfully deleted dataset:[/success] [highlight]{name}[/highlight]")
    else:
        console.print("[error]Error:[/error] No current working project found.", style="error")
    


# ── track subcommand group ──────────────────────────────────────────
track_app = typer.Typer(
    name="track",
    help="Register manually-created files into the project config so they are tracked just like MCP-created files.",
)
app.add_typer(track_app)


def _get_working_dir():
    """Resolve the current project and return a WorkingDirectory, or exit with an error."""
    pr = getcurrentProject()
    if pr is None:
        console.print(
            "[error]Error:[/error] No current working project found. "
            "Use [info]'automl set'[/info] or run from an initialised project directory.",
            style="error",
        )
        raise typer.Exit(1)
    return WorkingDirectory(pr.root)


@track_app.command(help="Register a pipeline element (.py) that already exists on disk, or update dependencies of an existing element.")
def pipeline(
    stage: Annotated[str, typer.Option("--stage", "-s", help="Pipeline stage this element belongs to (e.g. preprocessing, training)")],
    file: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to the .py file (absolute or relative to project root). Omit if only updating dependencies.",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Unique element name (defaults to file stem)")] = None,
    depends_on: Annotated[Optional[List[str]], typer.Option("--dep", "-d", help="Dependencies in 'stage.element' or 'utils.file' format")] = None,
    metadata: Annotated[Optional[List[str]], typer.Option("--meta", "-m", help="Key-value pairs like -m k=v")] = None,
):
    wd = _get_working_dir()
    
    if file is None:
        if name is None:
            console.print("[error]Error:[/error] If file is omitted, you must provide --name and --stage to update an existing element.")
            raise typer.Exit(1)
        element_name = name
        entry = wd.config.get(f"pipeline.stages.{stage}.elements.{name}")
        if not entry or "path" not in entry:
            console.print(f"[error]Error:[/error] Element {stage}.{name} not found in config. Cannot update dependencies without a file path.")
            raise typer.Exit(1)
        relative_path = Path(entry["path"])
    else:
        file = file.resolve()
        element_name = name or file.stem

        # Make path relative to project root
        try:
            relative_path = file.relative_to(wd.root)
        except ValueError:
            console.print(f"[error]Error:[/error] File must be inside the project root [info]{wd.root}[/info]")
            raise typer.Exit(1)

    meta = parse_key_value(metadata or [])

    try:
        with wd.manager:
            wd.manager.update_pipeline(
                stage=stage,
                name=element_name,
                path=relative_path,
                metadata=meta or None,
                depends_on=depends_on,
            )
        console.print(
            f"[success]Tracked pipeline element:[/success] "
            f"[highlight]{stage}.{element_name}[/highlight] → [info]{relative_path.as_posix()}[/info]"
        )
    except Exception as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@track_app.command(help="Register a utility file (.py) that already exists on disk")
def util(
    file: Annotated[
        Path,
        typer.Argument(
            help="Path to the .py file (absolute or relative to project root, must be inside utils/)",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Unique util name (defaults to file stem)")] = None,
    metadata: Annotated[Optional[List[str]], typer.Option("--meta", "-m", help="Key-value pairs like -m k=v")] = None,
):
    wd = _get_working_dir()
    file = file.resolve()
    util_name = name or file.stem

    try:
        relative_path = file.relative_to(wd.root)
    except ValueError:
        console.print(f"[error]Error:[/error] File must be inside the project root [info]{wd.root}[/info]")
        raise typer.Exit(1)

    meta = parse_key_value(metadata or [])

    try:
        with wd.manager:
            wd.manager.update_utils(
                name=util_name,
                path=relative_path,
                metadata=meta or None,
            )
        console.print(
            f"[success]Tracked util:[/success] [highlight]{util_name}[/highlight] → [info]{relative_path.as_posix()}[/info]"
        )
    except Exception as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@track_app.command(help="Register an analysis file (.py) that already exists on disk")
def analysis(
    file: Annotated[
        Path,
        typer.Argument(
            help="Path to the .py file (absolute or relative to project root, must be inside analysis/)",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Unique analysis name (defaults to file stem)")] = None,
    output_type: Annotated[Optional[str], typer.Option("--type", "-t", help="Output type: table, graph, list, or float")] = None,
    metadata: Annotated[Optional[List[str]], typer.Option("--meta", "-m", help="Key-value pairs like -m k=v")] = None,
):
    wd = _get_working_dir()
    file = file.resolve()
    analysis_name = name or file.stem

    try:
        relative_path = file.relative_to(wd.root)
    except ValueError:
        console.print(f"[error]Error:[/error] File must be inside the project root [info]{wd.root}[/info]")
        raise typer.Exit(1)

    meta = parse_key_value(metadata or [])

    try:
        with wd.manager:
            wd.manager.update_analysis(
                name=analysis_name,
                path=relative_path,
                output_type=output_type,
                metadata=meta or None,
            )
        console.print(
            f"[success]Tracked analysis:[/success] [highlight]{analysis_name}[/highlight] → [info]{relative_path.as_posix()}[/info]"
        )
    except Exception as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@track_app.command(name="delete-pipeline", help="Remove a pipeline element from config (and optionally from disk)")
def delete_pipeline(
    stage: Annotated[str, typer.Argument(help="Pipeline stage the element belongs to")],
    name: Annotated[str, typer.Argument(help="Name of the pipeline element to delete")],
    keep_file: Annotated[bool, typer.Option("--keep-file", "-k", help="Keep the file on disk, only remove from config")] = False,
):
    wd = _get_working_dir()

    try:
        if keep_file:
            # Only remove from config, don't delete the file
            with wd.manager:
                wd.manager.delete_element(stage, name)
        else:
            wd.delete_pipeline_element(stage=stage, name=name)
        console.print(
            f"[success]Deleted pipeline element:[/success] [highlight]{stage}.{name}[/highlight]"
            + (" [dim](file kept on disk)[/dim]" if keep_file else "")
        )
    except (KeyError, ValueError) as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@track_app.command(name="delete-util", help="Remove a utility file from config (and optionally from disk)")
def delete_util(
    name: Annotated[str, typer.Argument(help="Name of the utility to delete")],
    keep_file: Annotated[bool, typer.Option("--keep-file", "-k", help="Keep the file on disk, only remove from config")] = False,
):
    wd = _get_working_dir()

    try:
        if keep_file:
            with wd.manager:
                wd.manager.delete_utils(name)
        else:
            wd.delete_utils(name=name)
        console.print(
            f"[success]Deleted util:[/success] [highlight]{name}[/highlight]"
            + (" [dim](file kept on disk)[/dim]" if keep_file else "")
        )
    except (KeyError, ValueError) as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@track_app.command(name="delete-analysis", help="Remove an analysis file from config (and optionally from disk)")
def delete_analysis(
    name: Annotated[str, typer.Argument(help="Name of the analysis entry to delete")],
    keep_file: Annotated[bool, typer.Option("--keep-file", "-k", help="Keep the file on disk, only remove from config")] = False,
):
    wd = _get_working_dir()

    try:
        if keep_file:
            with wd.manager:
                wd.manager.delete_analysis(name)
        else:
            wd.delete_analysis(name=name)
        console.print(
            f"[success]Deleted analysis:[/success] [highlight]{name}[/highlight]"
            + (" [dim](file kept on disk)[/dim]" if keep_file else "")
        )
    except (KeyError, ValueError) as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@track_app.command(name="delete-ops", help="Remove an ops file entry from config")
def delete_ops_entry(
    name: Annotated[str, typer.Argument(help="Name of the ops entry to delete from config")],
):
    wd = _get_working_dir()

    try:
        wd.delete_ops(name=name)
        console.print(f"[success]Deleted ops entry:[/success] [highlight]{name}[/highlight]")
    except (KeyError, ValueError) as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@track_app.command(help="Show all files currently tracked in the project config")
def show():
    wd = _get_working_dir()
    print_header()
    cfg = wd.config

    has_content = False

    # ── Pipeline ──
    stages = cfg.get("pipeline.stages", {}) or {}
    if stages:
        has_content = True
        table = Table(title="Pipeline Elements", border_style="blue", header_style="bold cyan")
        table.add_column("Stage", style="highlight")
        table.add_column("Name", style="info")
        table.add_column("Path", style="success")
        table.add_column("Dependencies", style="dim")
        table.add_column("Metadata", style="dim")

        for stage_name, stage_data in stages.items():
            elements = stage_data.get("elements", {}) or {}
            for elem_name, elem_data in elements.items():
                deps = ", ".join(elem_data.get("depends_on", []) or []) or "—"
                meta = elem_data.get("metadata", {}) or {}
                meta_str = ", ".join(f"{k}={v}" for k, v in meta.items()) if meta else "—"
                table.add_row(stage_name, elem_name, str(elem_data.get("path", "—")), deps, meta_str)

        console.print(table)
        console.print()

    # ── Utils ──
    utils_files = cfg.get("utils.files", {}) or {}
    if utils_files:
        has_content = True
        table = Table(title="Utility Files", border_style="blue", header_style="bold cyan")
        table.add_column("Name", style="highlight")
        table.add_column("Path", style="info")
        table.add_column("Metadata", style="dim")

        for name, data in utils_files.items():
            meta = data.get("metadata", {}) or {}
            meta_str = ", ".join(f"{k}={v}" for k, v in meta.items()) if meta else "—"
            table.add_row(name, str(data.get("path", "—")), meta_str)

        console.print(table)
        console.print()

    # ── Analysis ──
    analysis_files = cfg.get("analysis.files", {}) or {}
    if analysis_files:
        has_content = True
        table = Table(title="Analysis Files", border_style="blue", header_style="bold cyan")
        table.add_column("Name", style="highlight")
        table.add_column("Path", style="info")
        table.add_column("Output Type", style="success")
        table.add_column("Metadata", style="dim")

        for name, data in analysis_files.items():
            meta = data.get("metadata", {}) or {}
            meta_str = ", ".join(f"{k}={v}" for k, v in meta.items()) if meta else "—"
            table.add_row(name, str(data.get("path", "—")), str(data.get("output_type", "—")), meta_str)

        console.print(table)
        console.print()

    # ── Datasets ──
    dataset_files = cfg.get("datasets.files", {}) or {}
    if dataset_files:
        has_content = True
        table = Table(title="Datasets", border_style="blue", header_style="bold cyan")
        table.add_column("Name", style="highlight")
        table.add_column("Source", style="info")
        table.add_column("Type", style="success")
        table.add_column("Description", style="dim")

        for name, data in dataset_files.items():
            table.add_row(
                name,
                str(data.get("source", "—")),
                str(data.get("type", "—")),
                str(data.get("description", "—")),
            )

        console.print(table)
        console.print()

    if not has_content:
        console.print("[warning]No tracked files found in the project config.[/warning]")


@track_app.command(help="Check if tracked config entries match actual files on disk")
def sync():
    wd = _get_working_dir()
    print_header()

    warnings = wd.check_sync()

    if not warnings:
        console.print("[success]✔ Everything is in sync![/success] All tracked files exist on disk.")
    else:
        console.print(f"[warning]Found {len(warnings)} issue(s):[/warning]\n")
        for w in warnings:
            console.print(f"  [error]✗[/error] {w}")
        console.print(
            "\n[dim]Tip: Use [bold]automl track pipeline / util / analysis[/bold] to fix missing entries, "
            "or remove stale entries from config.yaml manually.[/dim]"
        )


# ── end track subcommand group ──────────────────────────────────────


# ── meta subcommand group ───────────────────────────────────────────
meta_app = typer.Typer(
    name="meta",
    help="Manage top-level project metadata stored in config.yaml.",
)
app.add_typer(meta_app)


@meta_app.command(name="set", help="Set or update project metadata key-value pairs")
def meta_set(
    pairs: Annotated[
        List[str],
        typer.Argument(help="One or more key=value pairs, e.g. author=Alice version=1.0"),
    ],
):
    wd = _get_working_dir()
    updates = parse_key_value(pairs)

    if not updates:
        console.print("[error]Error:[/error] No valid key=value pairs provided.")
        raise typer.Exit(1)

    try:
        wd.update_metadata(updates)
        for k, v in updates.items():
            console.print(f"  [success]✔[/success] [highlight]{k}[/highlight] = [info]{v}[/info]")
        console.print(f"\n[success]Updated {len(updates)} metadata key(s).[/success]")
    except Exception as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


@meta_app.command(name="get", help="Show project metadata (all keys or a specific key)")
def meta_get(
    key: Annotated[Optional[str], typer.Argument(help="Specific metadata key to retrieve (omit for all)")] = None,
):
    wd = _get_working_dir()
    print_header()

    if key is not None:
        value = wd.get_metadata(key)
        if value is None:
            console.print(f"[warning]No metadata found for key:[/warning] [highlight]{key}[/highlight]")
        else:
            console.print(f"[highlight]{key}[/highlight] = [info]{value}[/info]")
    else:
        meta = wd.get_metadata() or {}
        if not meta:
            console.print("[warning]No project metadata has been set yet.[/warning]")
        else:
            table = Table(title="Project Metadata", border_style="blue", header_style="bold cyan")
            table.add_column("Key", style="highlight")
            table.add_column("Value", style="info")

            for k, v in meta.items():
                table.add_row(str(k), str(v))

            console.print(table)


@meta_app.command(name="delete", help="Delete a metadata key from the project config")
def meta_delete(
    key: Annotated[str, typer.Argument(help="The metadata key to remove")],
):
    wd = _get_working_dir()

    try:
        wd.delete_metadata(key)
        console.print(f"[success]Deleted metadata key:[/success] [highlight]{key}[/highlight]")
    except ValueError as e:
        console.print(f"[error]Error:[/error] {e}")
        raise typer.Exit(1)


# ── end meta subcommand group ───────────────────────────────────────

@app.command(help="Recreate a dashboard item by rerunning its analysis script")
def recreate(
    script_name: Annotated[str, typer.Argument(help="Name of the analysis script (without .py)")]
):
    wd = _get_working_dir()
    
    dashboard_dir = wd.root / "dashboard_runs"
    meta_file = dashboard_dir / "metadata.json"
    
    if not meta_file.exists():
        console.print("[error]Error:[/error] No dashboard metadata found.")
        raise typer.Exit(1)
        
    try:
        metadata = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[error]Error reading metadata:[/error] {e}")
        raise typer.Exit(1)
        
    scripts = metadata.get("scripts", {})
    
    target_key = None
    for script_key in scripts:
        if Path(script_key).stem == script_name:
            target_key = script_key
            break
            
    if target_key is None:
        console.print(f"[error]Error:[/error] Script '{script_name}' not found in dashboard metadata.")
        raise typer.Exit(1)
        
    variables = list(scripts[target_key].keys())
    
    if not variables:
        console.print(f"[warning]Warning:[/warning] No variables tracked for '{script_name}'.")
        raise typer.Exit(1)
        
    console.print(f"[info]Rerunning '{script_name}' to capture: {', '.join(variables)}...[/info]")
    
    from dist_automl.dashboard_maker_custom.dashboard_capture import capture_script_outputs
    
    try:
        script_path = wd.root / "analysis" / f"{script_name}.py"
        if not script_path.exists():
            console.print(f"[error]Error:[/error] Script file '{script_path}' does not exist.")
            raise typer.Exit(1)
            
        captured = capture_script_outputs(
            project_root=wd.root,
            script_path=script_path,
            variables=variables
        )
        
        file_content = script_path.read_text(encoding="utf-8")
        wd.update_analysis(
            name=script_name, 
            path=Path(f"analysis/{script_name}.py"), 
            metadata=captured, 
            content=file_content, 
            overwrite=True
        )
        
        console.print(f"[success]Successfully recreated dashboard items for '{script_name}'.[/success]")
    except Exception as e:
        console.print(f"[error]Error recreating dashboard items:[/error] {e}")
        raise typer.Exit(1)


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


# ── mcp subcommand group ────────────────────────────────────────────
mcp_app = typer.Typer(
    name="mcp",
    help="MCP server management: show config or start the server.",
    invoke_without_command=True,
)
app.add_typer(mcp_app)


@mcp_app.callback(invoke_without_command=True)
def mcp_default(ctx: typer.Context):
    """
    Show the MCP client configuration JSON (default when no subcommand is given).
    Copy this into your MCP client settings to connect.
    """
    if ctx.invoked_subcommand is not None:
        return

    from dist_automl.mcp_server import MCP_HOST, MCP_PORT

    schema = {
        "mcpServers": {
            "Auto_ML": {
                "url": f"http://{MCP_HOST}:{MCP_PORT}/mcp"
            }
        }
    }

    print_header()
    console.print(Panel(
        "[bold cyan]MCP Server Configuration (HTTP)[/bold cyan]\n"
        "Copy the following JSON into your MCP client settings file.",
        border_style="blue",
    ))

    richprint(schema, color="green", json_=True)

    console.print(
        f"\n[dim]The MCP server listens on [bold]http://{MCP_HOST}:{MCP_PORT}/mcp[/bold] "
        f"(streamable-http transport).[/dim]"
    )
    console.print(
        "[dim]Tip: Run [bold]automl mcp start[/bold] to launch the server.[/dim]"
    )


@mcp_app.command(name="start", help="Start the MCP server over HTTP")
def mcp_start(
    host: Annotated[str, typer.Option("--host", "-h", help="Host to bind to")] = None,
    port: Annotated[int, typer.Option("--port", "-p", help="Port to listen on")] = None,
):
    """Launch the MCP server using streamable-http transport."""
    from dist_automl.mcp_server import server, MCP_HOST, MCP_PORT

    use_host = host or MCP_HOST
    use_port = port or MCP_PORT

    import socket

    if not (1 <= use_port <= 65535):
        console.print(f"[error]Error:[/error] Port must be between 1 and 65535. Got {use_port}.")
        raise typer.Exit(1)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((use_host, use_port))
    except socket.gaierror:
        console.print(f"[error]Error:[/error] Invalid host address: '{use_host}'")
        raise typer.Exit(1)
    except OSError as e:
        # 98 is EADDRINUSE on POSIX, 10048 is WSAEADDRINUSE on Windows
        if e.errno in (98, 10048):
            console.print(f"[error]Error:[/error] Port {use_port} is already in use on {use_host}.")
        else:
            console.print(f"[error]Error:[/error] Cannot bind to {use_host}:{use_port} ({e.strerror}).")
        raise typer.Exit(1)

    print_header()
    console.print(
        f"[success]Starting MCP server at "
        f"[bold]http://{use_host}:{use_port}/mcp[/bold][/success]"
    )
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    server.run(
        transport="streamable-http",
        host=use_host,
        port=use_port,
    )


# ── end mcp subcommand group ────────────────────────────────────────


if __name__ == "__main__":
    app()
