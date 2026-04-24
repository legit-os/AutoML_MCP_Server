from pathlib import Path
import subprocess
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

@server.tool(tags=serverstate.state_options)
def change_tool_list(state: Literal["info_and_file_reading","file_writing","analysis_and_dashboard"]):
    """
    Use this tool to access other tools that the server provides:
    
    info_and_file_reading : provides project info, how to use guide, file running and reading tools
    file_writing : provides tools to write any type of file
    analysis_and_dashboard : provides tools to write analysis code and create dashboard widget
    """
    
    if state == "info_and_file_reading":
        serverstate.state  = "info"
        server.enable(tags={"info"},only=True)
    elif state == "analysis_and_dashboard":
        serverstate.state = "dashboard"
        server.enable(tags={"dashboard"},only=True)
    elif state == "file_writing":
        serverstate.state = "file"
        server.enable(tags={"file"},only=True)
    
    server.enable(names={serverstate.state_changer})
    
    return "Enabled requested tools and disabled others, you can check the tools exposed to you"

@server.tool(tags={"info"})
def get_current_project_info():
    """
    Get the Projects info that is stored in the config file of the Project
    """
    
    info = {}
    
    info["system"] = sys.platform
    
    info["project_root"] = wd.root.__str__()
    
    
    info["config"] = (wd._config_path).read_text()
    
    return info
    
    

# @server.tool(tags={"info"})
# def run_file(file_path: str, timeout: float, arguments: list[str] = None):
#     """Run a file you created, assuming that the file captures arguments provided 
#     from command line, you can provide arguments that your file requires.
#     File Path should be provided relative to project like 'pipeline/scaler.py'.
#     Timeout must be provided so that system doesn't break if python files have bugs
#     """
#     cmd = ["uv", "run", file_path]
#     if arguments:
#         cmd.extend(arguments)
    
#     try:
#         out = subprocess.run(
#             cmd,
#             timeout=timeout,
#             cwd=cwp_path,
#             capture_output=True,
#             text=True
#         )
        
#         status = "Success" if out.returncode == 0 else "Failure"
#         result = f"--- Execution {status} (Return Code: {out.returncode}) ---\n"
#         if out.stdout:
#             result += f"\nSTDOUT:\n{out.stdout}"
#         if out.stderr:
#             result += f"\nSTDERR:\n{out.stderr}"
#         return result
        
#     except subprocess.TimeoutExpired:
#         return f"Error: Execution timed out after {timeout} seconds."
#     except Exception as e:
#         return f"Error: An unexpected error occurred: {str(e)}"

@server.tool(tags={"info"})
def read_file(path: str):
    """
    Read a file from the project. 
    'path' should be in the format 'stage.element' for pipeline files (e.g., 'preprocessing.scaler')
    or 'utils.name' for utility files (e.g., 'utils.helper').
    """
    if "." not in path:
        return "Error: Path must be in 'stage.element' or 'utils.name' format."
        
    parts = path.split(".", 1)
    prefix = parts[0]
    name = parts[1]
    
    file_info = None
    if prefix == "utils":
        file_info = wd.config.get(f"utils.files.{name}")
    else:
        file_info = wd.config.get(f"pipeline.stages.{prefix}.elements.{name}")
        
    if not file_info or "path" not in file_info:
        return f"Error: Could not find file registered for '{path}' in config."
        
    rel_path = Path(file_info["path"])
    abs_path = cwp_path / rel_path
    
    if not abs_path.exists():
        return f"Error: File '{rel_path}' exists in config but not on disk."
        
    try:
        return abs_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"
        

# @server.tool()
# def how_to_use_guide():
#     return """
    

# """




@server.tool(tags={"file"})
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
    
    wd.update_pipeline_element(stage=stage,name=name,content=content,
                               path=Path(f"pipeline/{name}.py"),
                               depends_on=depends_on,
                               metadata=metadata,
                               overwrite=overwrite)
    return "Updated config file, you can view project info to confirm"

@server.tool(tags={"file"})
def write_util(name: str, content: str, overwrite : bool = False, metadata: dict = None):
    "Write helper files for the pipeline"
    
    wd.update_utils(name=name, path=Path(f"utils/{name}.py"),
                    metadata=metadata, content=content,overwrite=overwrite)
    
    return "Updated, you can view project info to confirm"

@server.tool(tags={"file"})
def manage_experiment_notebook(action: Literal["read", "add", "edit", "delete"], 
                               index: int = None, 
                               content: str = None, 
                               cell_type: Literal["code", "markdown"] = "code"):
    """
    Manage cells in the experiment.ipynb notebook located at the project root.
    Actions: 
    - read: Returns all cells or a specific cell if index is provided.
    - add: Adds a new cell at index (or end if index is None).
    - edit: Overwrites cell content at index.
    - delete: Removes cell at index.
    """
    return wd.manage_notebook_cell(action=action, index=index, content=content, cell_type=cell_type)

# @server.tool()
# def write_file(file_type:Literal["util","pipeline_element"],
#                name: str,
#                content: str,
#                stage:Literal["utils","splitting","preprocessing","scaling","training","evalutaion","serving"],
#                depends_on: list[str] = None,
#                overwrite: bool = False,
#                metadata: dict = None):
#     """Write a utility or pipeline file.
#     Args: 
#         file_type: util or pipeline_element 
#         name: without extention name of the file
#         content: code to write in the file
#         stage: only required for the pipeline element
#         depends_on: stage.name or util.name (for only those files that already exists in the config file)
#         metadata: a dictionary of extra data assumed str to (str or int) mapping
#         """
#     if file_type == "pipeline_element":
#         if stage == "utils":
#             raise ValueError("Utils name of stage should be given on")
#         return write_pipeline_element(stage=stage,name=name,
#                                       content=content,
#                                       overwrite=overwrite,
#                                       depends_on=depends_on,
#                                       metadata=metadata)
#     elif file_type == "util":
#         return write_util(name=name,content=content,overwrite=overwrite,metadata=metadata)

@server.tool(tags={"file"})
def delete_pipeline_element(stage:str,name:str):
    "delete a file from the pipeline"
    
    wd.delete_pipeline_element(stage=stage, name=name)

    return "Deleted a file, you can view project info to confirm"


@server.tool(tags={'file'})
def delete_util(name:str):
    "delete a utility file"
    wd.delete_utils(name=name)
    
    return "Deleted utility file, you can view project info to confirm"

# @server.tool()
# def delete_file(file_type : Literal["util","pipeline_element"],name: str,
#                 stage:Literal["utils","splitting","preprocessing","scaling","training","evalutaion","serving"]):
#     """
#     delete a utility or pipeline element
#     Args: 
#         file_type: required as given in definition
#         name: without extention name of the file
#         stage: required only for the pipeline element else should be given as utils
#     """
    
    
#     if file_type == "pipeline_element":
#         delete_pipeline_element(stage,name)
#     elif file_type == "util":
#         delete_util(name)



@server.tool(tags={"dashboard"})
def create_analysis_dashboard_item(name: str,file_content: str, capture_variables: list[str]):
    """
    create a file that produces some variable containing pandas dataframe or matplotlib 
    figure objects or list or dictionaries that will show on the dashboard.
    It only reads the variables from the file that are given in 'capture_variables' argument.
    """
    
    script_path = cwp_path / "analysis" / f"{name}.py"
    
    # Write the analysis script to disk first
    wd.update_analysis(name=name, path=Path(f"analysis/{name}.py"), metadata={}, content=file_content)
    # Then run it and capture the specified variables
    captured = capture_script_outputs(project_root=cwp_path, script_path=script_path, variables=capture_variables)
    # Update metadata with what was captured
    wd.update_analysis(name=name, path=Path(f"analysis/{name}.py"), metadata=captured, content=file_content)
    return "captured provided variables and added to dashboard"
    
    
    
    
# server.enable(tags={serverstate.info},only=True)
server.disable(names={serverstate.state_changer})

if __name__ == "__main__":
    server.run()