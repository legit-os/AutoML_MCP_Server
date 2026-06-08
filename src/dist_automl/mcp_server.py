from pathlib import Path
import sys
from typing import Literal

from fastmcp import FastMCP
from dist_automl.working_dir import WorkingDirectory
from dist_automl.dashboard_maker_custom.dashboard_capture import capture_script_outputs

cwp_path = (Path(__file__).parent / "managers" / "current_project_root.txt").read_text()

if cwp_path is None:
    raise FileNotFoundError("Initialize a project on which this MCP server will run")
else:
    cwp_path = Path(cwp_path)

wd = WorkingDirectory(project_root=cwp_path)

server = FastMCP(
    name="Auto ML",instructions="""
                 This server Provides tools to help a user build an end to end 
                 Machine Learning System from analysis to deployment.
                 You have tools to write down some selected files and run them.
                 It is highly recommended to use sys.argv in the pipeline python files
                 to capture a list of arguments for running a file so the files are reusable.
                 You an write utility files, analysis files and the main pipeline files.
                 Analysis files will create a dashboard so you need to write code according to the tool instruction.
                 
                 IMPORTANT: At the start of every session, read the 'agent.md' file in 
                 the project root using the read_file tool. It contains project-specific 
                 best practices and guidelines you must follow.
                 """
                 )


class ServerState():
    def __init__(self):
        self.info = "info"
        self.file = "file"
        self.dash = "dashboard"
        self.state = self.info
        self.state_options = {self.info, self.file, self.dash}
        self.state_changer = "change_tool_list"
        

serverstate = ServerState()

@server.tool(tags=serverstate.state_changer)
def change_tool_list(state: Literal["info_and_file_reading","file_writing","analysis_and_dashboard"]):
    """
    Use this tool to access other tools that the server provides:
    
    info_and_file_reading : provides project info, how to use guide, file running and reading tools
    file_writing : provides tools to write any type of file
    analysis_and_dashboard : provides tools to write analysis code and create dashboard widget
    """
    
    if state == "info_and_file_reading":
        serverstate.state  = "info"
        server.enable(tags={serverstate.info},only=True)
    elif state == "analysis_and_dashboard":
        serverstate.state = "dashboard"
        server.enable(tags={serverstate.dash},only=True)
    elif state == "file_writing":
        serverstate.state = "file"
        server.enable(tags={serverstate.file},only=True)
    
    server.enable(names={serverstate.state_changer})
    
    return "Enabled requested tools and disabled others, you can check the tools exposed to you"

@server.tool(tags={serverstate.info})
def get_current_project_info():
    """
    Get the Projects info that is stored in the config file of the Project
    """
    try:
        info = {}
        info["system"] = sys.platform
        info["project_root"] = wd.root.__str__()
        info["config"] = (wd._config_path).read_text()
        return info
    except Exception as e:
        return f"Error: {e}"


@server.tool(tags=serverstate.state_options)
def manage_plan(action: Literal["read", "rewrite", "append"], content: str = None):
    """
    Manage the agentplan.md planning file in the project root.
    Use this to plan your approach before making changes, then present 
    it to the user for review and approval.
    
    Args:
        action: The operation to perform.
        content: Markdown content for 'rewrite' or 'append' actions.
    
    Actions:
    - read: Returns the current contents of agentplan.md (or a message if it doesn't exist).
    - rewrite: Creates or overwrites agentplan.md with the provided content.
    - append: Appends the provided content to the end of agentplan.md (creates it if needed).
    """
    try:
        plan_path = cwp_path / "agentplan.md"
        
        if action == "read":
            if not plan_path.exists():
                return "No agentplan.md file exists yet. Use 'rewrite' or 'append' to create one."
            return plan_path.read_text(encoding="utf-8")
        
        if content is None:
            return "Error: 'content' is required for 'rewrite' and 'append' actions."
        
        if action == "rewrite":
            plan_path.write_text(content, encoding="utf-8")
            return "Successfully created/updated agentplan.md"
        
        elif action == "append":
            existing = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
            separator = "\n\n" if existing and not existing.endswith("\n") else ("\n" if existing else "")
            plan_path.write_text(existing + separator + content, encoding="utf-8")
            return "Successfully appended to agentplan.md"
    except Exception as e:
        return f"Error: {e}"

def _resolve_path(path: str) -> Path:
    """Resolve a path string to an absolute path, checking config names as fallback."""
    abs_path = cwp_path / path
    
    if not abs_path.exists() and "." in path:
        parts = path.split(".", 1)
        prefix = parts[0]
        name = parts[1]
        
        file_info = None
        if prefix == "utils":
            file_info = wd.config.get(f"utils.files.{name}")
        else:
            file_info = wd.config.get(f"pipeline.stages.{prefix}.elements.{name}")
            
        if file_info and "path" in file_info:
            abs_path = cwp_path / file_info["path"]
    
    return abs_path


@server.tool(tags={serverstate.info})
def read_file(path: str, start_line: int = None, end_line: int = None):
    """
    Read a file from the project with optional line range.
    
    Args:
        path: Path to the file. Can be:
              - Relative to project root (e.g. 'pipeline/scaler.py', 'Dockerfile')
              - A registered name like 'stage.element' (e.g. 'preprocessing.scaler')
                or 'utils.helper'
        start_line: First line to return (1-indexed, inclusive). Omit to start from beginning.
        end_line: Last line to return (1-indexed, inclusive). Omit to read until end.
    
    Returns the file content with line numbers prefixed (e.g. '  1: import os').
    When start_line/end_line are provided, only the requested range is returned.
    """
    abs_path = _resolve_path(path)
    
    if not abs_path.exists():
        return f"Error: '{path}' does not exist relative to project root or as a registered element."
    
    if not abs_path.is_file():
        return f"Error: '{path}' is not a file. Use ls_dir to list directory contents."
    
    try:
        lines = abs_path.read_text(encoding="utf-8").splitlines()
        total = len(lines)
        
        # Default to full file
        start = 1
        end = total
        
        if start_line is not None:
            start = max(1, start_line)
        if end_line is not None:
            end = min(total, end_line)
        
        if start > total:
            return f"Error: start_line {start} exceeds total lines ({total})."
        if start > end:
            return f"Error: start_line ({start}) is greater than end_line ({end})."
        
        # Build line-numbered output
        width = len(str(end))
        selected = lines[start - 1 : end]
        numbered = [f"{str(i).rjust(width)}: {line}" for i, line in enumerate(selected, start=start)]
        
        header = f"File: {path} | Lines {start}-{end} of {total}"
        return header + "\n" + "\n".join(numbered)
    
    except Exception as e:
        return f"Error reading file: {str(e)}"


@server.tool(tags={serverstate.info})
def ls_dir(path: str = ".", depth: int = 1):
    """
    List directory contents from the project with controllable depth.
    
    Args:
        path: Directory path relative to project root. Defaults to '.' (project root).
        depth: How many levels deep to list (1 = immediate children, 2 = children + grandchildren, etc.).
               Use -1 for unlimited depth.
    
    Output format shows type, relative path, and indentation by level:
      [DIR]  pipeline/
      [FILE] pipeline/scaler.py
    """
    abs_path = cwp_path / path
    
    if not abs_path.exists():
        return f"Error: Directory '{path}' does not exist."
    
    if not abs_path.is_dir():
        return f"Error: '{path}' is not a directory. Use read_file to read files."
    
    try:
        items = []
        _ls_recursive(abs_path, abs_path, depth, 0, items)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def _ls_recursive(base: Path, current: Path, max_depth: int, current_depth: int, result: list):
    """Recursively list directory contents up to max_depth."""
    if max_depth != -1 and current_depth >= max_depth:
        return
    
    try:
        entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return
    
    indent = "  " * current_depth
    
    for entry in entries:
        # Skip hidden/system directories
        if entry.name.startswith(".") and entry.is_dir():
            continue
        if entry.name == "__pycache__":
            continue
            
        relative = entry.relative_to(base)
        
        if entry.is_dir():
            result.append(f"{indent}[DIR]  {relative.as_posix()}/")
            _ls_recursive(base, entry, max_depth, current_depth + 1, result)
        else:
            result.append(f"{indent}[FILE] {relative.as_posix()}")


@server.tool(tags={serverstate.file})
def write_pipeline_element(stage: str, name: str, content: str,
                           depends_on:list[str] = None,
                           metadata: dict = None,
                           overwrite: bool = False ):
    '''
    Create a file that works in the main pipeline, write the content for the file in
    such a way so that it can be used by importing a function or class from the 
    file or can directly run from the command line.
    Arguments:
        stage: represents the stage of the machine learning cycle for which the file works
        name: name of the this process in the pipeline (must be unique)
        depends_on: accepts strings like 'utils.helper' or 'preprocessing.col_mixer' assuming that the names provided exist and are in the config file
    '''
    try:
        wd.update_pipeline_element(stage=stage,name=name,content=content,
                                   path=Path(f"pipeline/{name}.py"),
                                   depends_on=depends_on,
                                   metadata=metadata,
                                   overwrite=overwrite)
        return "Updated config file, you can view project info to confirm"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.file})
def write_util(name: str, content: str, overwrite : bool = False, metadata: dict = None):
    "Write helper files for the pipeline"
    try:
        wd.update_utils(name=name, path=Path(f"utils/{name}.py"),
                        metadata=metadata, content=content,overwrite=overwrite)
        return "Updated, you can view project info to confirm"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.file})
def manage_notebook(action: Literal["read", "add", "edit", "delete"], 
                    notebook: str = None,
                    index: int = None, 
                    content: str = None, 
                    cell_type: Literal["code", "markdown"] = "code"):
    """
    Manage cells in a Jupyter notebook inside the project.
    
    Args:
        action: The operation to perform on the notebook.
        notebook: Path to the .ipynb file relative to the project root
                  (e.g. 'experiment.ipynb' or 'notebooks/analysis.ipynb').
                  Defaults to 'experiment.ipynb' if not provided.
        index: Cell index (0-based). Required for 'edit' and 'delete'.
               Optional for 'read' (reads specific cell) and 'add' (inserts at position).
        content: Cell source content. Required for 'add' and 'edit'.
        cell_type: Type of cell to create when using 'add'.
    
    Actions: 
    - read: Returns all cells or a specific cell if index is provided.
    - add: Adds a new cell at index (or end if index is None). Creates the notebook if it doesn't exist.
    - edit: Overwrites cell content at index.
    - delete: Removes cell at index.
    """
    return wd.manage_notebook_cell(action=action, notebook=notebook,
                                   index=index, content=content, cell_type=cell_type)

@server.tool(tags={serverstate.info})
def list_notebooks():
    """
    List all Jupyter notebook (.ipynb) files found in the project.
    Returns their names and relative paths so you can pass them to manage_notebook.
    """
    try:
        notebooks = wd.list_notebooks()
        if not notebooks:
            return "No .ipynb notebooks found in the project."
        return notebooks
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.file})
def delete_pipeline_element(stage:str,name:str):
    "delete a file from the pipeline"
    try:
        wd.delete_pipeline_element(stage=stage, name=name)
        return "Deleted a file, you can view project info to confirm"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.file})
def delete_util(name:str):
    "delete a utility file"
    try:
        wd.delete_utils(name=name)
        return "Deleted utility file, you can view project info to confirm"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.info})
def register_dataset(name: str, source: str, dtype: str = None, description: str = None, metadata: dict = None):
    """
    Add or update a dataset in the project configuration.
    
    Args:
        name: Unique name for the dataset
        source: Path to the dataset file or a descriptive source string
        dtype: Type of the dataset (e.g., 'csv', 'parquet', 'json')
        description: A brief description of the dataset
        metadata: Additional key-value pairs of metadata
    """
    try:
        wd.update_dataset(
            name=name,
            source=source,
            dtype=dtype,
            description=description,
            metadata=metadata
        )
        return f"Successfully registered dataset: {name}"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.info})
def delete_dataset(name: str):
    """
    Delete a dataset from the project configuration.
    """
    try:
        wd.delete_dataset(name)
        return f"Successfully deleted dataset: {name}"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.info})
def update_project_metadata(updates: dict):
    """
    Set or update top-level project metadata key-value pairs in the config.
    
    Args:
        updates: A dictionary of key-value pairs to set or update.
                 Values can be strings, numbers, booleans, lists, or dicts.
    
    Example: {"author": "Alice", "version": "1.0", "description": "My ML project"}
    """
    try:
        wd.update_metadata(updates)
        return f"Successfully updated project metadata: {list(updates.keys())}"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.info})
def get_project_metadata(key: str = None):
    """
    Get project-level metadata from the config.
    
    Args:
        key: Optional specific key to retrieve. Returns all metadata if not provided.
    """
    try:
        result = wd.get_metadata(key)
        if result is None and key is not None:
            return f"No metadata found for key: '{key}'"
        if not result:
            return "No project metadata has been set yet."
        return result
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.info})
def delete_project_metadata(key: str):
    """
    Delete a specific key from the project-level metadata.
    
    Args:
        key: The metadata key to remove.
    """
    try:
        wd.delete_metadata(key)
        return f"Successfully deleted metadata key: '{key}'"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.file})
def manage_ops_file(
    action: Literal["write", "append", "read"],
    file_path: str,
    content: str = None,
    track: bool = False,
    name: str = None,
    description: str = None,
    metadata: dict = None,
):
    """
    Manage ops/infrastructure files like Dockerfiles, DVC configs, CI/CD pipelines,
    docker-compose files, Makefiles, shell scripts, etc.
    
    These files live anywhere in the project and can optionally be tracked in the
    config under the 'ops' section.
    
    Args:
        action: The operation to perform.
        file_path: Path relative to project root (e.g. 'Dockerfile', 'docker-compose.yml', '.dvc/config').
        content: File content for 'write' and 'append' actions.
        track: If True, registers the file in the config 'ops' section (only used with 'write').
        name: Tracking name in config (defaults to file stem). Only used when track=True.
        description: Brief description of the file. Only used when track=True.
        metadata: Extra key-value metadata. Only used when track=True.
    
    Actions:
    - write: Creates or overwrites the file with the provided content.
    - append: Appends content to an existing file.
    - read: Returns the file contents.
    """
    try:
        if action == "write":
            if content is None:
                return "Error: 'content' is required for 'write' action."
            result_path = wd.write_ops_file(
                file_path=file_path,
                content=content,
                name=name,
                description=description,
                metadata=metadata,
                track=track,
            )
            tracked_msg = " and tracked in config" if track else ""
            return f"Successfully created '{result_path}'{tracked_msg}."
        
        elif action == "append":
            if content is None:
                return "Error: 'content' is required for 'append' action."
            wd.append_ops_file(file_path=file_path, content=content)
            return f"Successfully appended to '{file_path}'."
        
        elif action == "read":
            return wd.read_ops_file(file_path=file_path)
    
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.file})
def delete_analysis(name: str):
    """
    Delete an analysis file from the project (removes from config and disk).
    
    Args:
        name: Name of the analysis entry to delete.
    """
    try:
        wd.delete_analysis(name=name)
        return f"Deleted analysis file: {name}"
    except Exception as e:
        return f"Error: {e}"

@server.tool(tags={serverstate.dash})
def create_analysis_dashboard_item(name: str,file_content: str, capture_variables: list[str]):
    """
    create a file that produces some variable containing pandas dataframe or matplotlib 
    figure objects or list or dictionaries that will show on the dashboard.
    It only reads the variables from the file that are given in 'capture_variables' argument.
    """
    try:
        script_path = cwp_path / "analysis" / f"{name}.py"
        
        wd.update_analysis(name=name, path=Path(f"analysis/{name}.py"), metadata={}, content=file_content)
        captured = capture_script_outputs(project_root=cwp_path, script_path=script_path, variables=capture_variables)
        wd.update_analysis(name=name, path=Path(f"analysis/{name}.py"), metadata=captured, content=file_content)
        return "captured provided variables and added to dashboard"
    except Exception as e:
        return f"Error: {e}"


@server.tool(tags={serverstate.dash})
def read_dashboard_items(
    action: Literal["list", "read"],
    script_name: str = None,
    variable: str = None,
    max_rows: int = 50,
):
    """
    List or read dashboard items that were created by create_analysis_dashboard_item.

    Args:
        action: 'list' to see all items, 'read' to fetch a specific item's data.
        script_name: Analysis script name (stem only, e.g. 'eda' not 'eda.py').
                     Optional for 'list' (filters by script). Required for 'read'.
        variable: Variable name to read. Required for 'read'.
        max_rows: For dataframes, limit the number of rows returned (default 50).

    Actions:
    - list: Returns all dashboard items grouped by script, showing variable name,
            type, and file path for each. If script_name is given, lists only
            items from that script.
    - read: Returns the stored data for a specific variable. Works for dataframes,
            lists, dicts, and kpi numbers. For figures (images), returns the file
            path instead of content since images cannot be returned as text.
    """
    import json as _json

    dashboard_dir = cwp_path / "dashboard_runs"
    meta_file = dashboard_dir / "metadata.json"

    if not meta_file.exists():
        return "No dashboard data exists yet. Use create_analysis_dashboard_item to create items first."

    try:
        metadata = _json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception as e:
        return f"Error reading dashboard metadata: {e}"

    scripts = metadata.get("scripts", {})
    if not scripts:
        return "Dashboard metadata exists but contains no items."

    # --- LIST ---
    if action == "list":
        result = {}
        for script_key, variables in scripts.items():
            stem = Path(script_key).stem
            if script_name is not None and stem != script_name:
                continue
            items = []
            for var_name, var_info in variables.items():
                items.append({
                    "variable": var_name,
                    "type": var_info.get("type", "unknown"),
                    "path": var_info.get("path", ""),
                })
            result[stem] = items

        if not result:
            if script_name:
                return f"No dashboard items found for script '{script_name}'."
            return "No dashboard items found."

        return {"dashboard_items": result}

    # --- READ ---
    if action == "read":
        if not script_name or not variable:
            return "Error: 'script_name' and 'variable' are required for 'read' action."

        # Find the matching script key (compare by stem)
        target_key = None
        for script_key in scripts:
            if Path(script_key).stem == script_name:
                target_key = script_key
                break

        if target_key is None:
            available = [Path(k).stem for k in scripts]
            return f"Error: Script '{script_name}' not found. Available scripts: {available}"

        var_info = scripts[target_key].get(variable)
        if var_info is None:
            available = list(scripts[target_key].keys())
            return f"Error: Variable '{variable}' not found in script '{script_name}'. Available: {available}"

        var_type = var_info.get("type", "unknown")
        rel_path = var_info.get("path", "")

        if var_type == "figure":
            abs_path = dashboard_dir / rel_path
            return {
                "script": script_name,
                "variable": variable,
                "type": "figure",
                "note": "Image content is not returned, if your image has some plot try reading the data instead.",
                "file_path": str(abs_path),
            }

        data_path = dashboard_dir / rel_path
        if not data_path.exists():
            return f"Error: Data file not found at '{rel_path}'."

        try:
            data = _json.loads(data_path.read_text(encoding="utf-8"))
        except Exception as e:
            return f"Error reading data file: {e}"

        # For dataframes, truncate rows if needed
        if var_type == "dataframe" and isinstance(data, dict) and "rows" in data:
            total_rows = len(data["rows"])
            if total_rows > max_rows:
                data["rows"] = data["rows"][:max_rows]
                data["truncated"] = True
                data["total_rows"] = total_rows
                data["showing_rows"] = max_rows

        return {
            "script": script_name,
            "variable": variable,
            "type": var_type,
            "data": data,
        }

    return f"Error: Unknown action '{action}'. Use 'list' or 'read'."


# server.enable(tags={serverstate.info},only=True)
server.disable(names={serverstate.state_changer})

MCP_HOST = "127.0.0.1"
MCP_PORT = 9000

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host=MCP_HOST,
        port=MCP_PORT,
    )