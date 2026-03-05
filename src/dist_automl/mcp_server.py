from pathlib import Path
import subprocess
import sys

from fastmcp import FastMCP
from dist_automl.working_dir import WorkingDirectory
from dist_automl.dashboard_maker.dashboard_capture import capture_script_outputs

cwp_path = (Path(__file__).parent / "managers" / "current_project_root.txt").read_text()

if cwp_path is None:
    raise FileNotFoundError("Initialize a project on which this MCP server will run")
else:
    cwp_path = Path(cwp_path)

wd = WorkingDirectory(project_root=cwp_path)

server = FastMCP(name="Auto ML",instructions="""
                 This server Provides tools to help a user build an end to end 
                 Machine Learning System from analysis to deployment.
                 You have tools to write down some selected files and run them.
                 It is highly recommended to use sys.argv in the pipeline python files
                 to capture a list of arguments for running a file so the files are reusable.
                 You an write utility files, analysis files and the main pipeline files.
                 Analysis files will create a dashboard so you need to write code according to the tool instruction.
                 """)


@server.tool()
def get_current_project_info():
    """
    Get the Projects info that is stored in the config file of the Project
    """
    
    info = {}
    
    info["system"] = sys.platform
    
    info["project_root"] = wd.root.__str__()
    
    
    info["config"] = (wd._config_path).read_text()
    
    return info
    
    

@server.tool()
def run_file(file_path : str, timeout:float, arguments : list[str] = None):
    """Run a file you created, assuming that the file captures arguments provided 
    from command line, you can provide arguments that your file requires.
    File Path should be provided relative to project like 'pipeline/scaler.py'.
    Timeout must be provided so that system doesn't break if python files have bugs
    """
    if arguments is not None:
        subprocess.run(["uv","run",f"{file_path}"].extend(arguments),timeout=timeout,cwd=cwp_path)
    else:
        subprocess.run(["uv","run",f"{file_path}"],timeout=timeout,cwd=cwp_path)
        

# @server.tool()
# def how_to_use_guide():
#     return """
    

# """






@server.tool()
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

@server.tool()
def delete_pipeline_element(stage:str,name:str):
    "delete a file from the pipeline"
    
    wd.delete_pipeline_element(stage=stage, name=name)

    return "Deleted a file, you can view project info to confirm"




@server.tool()
def write_util(name: str, content: str, overwrite : bool = False, metadata: dict = None):
    "Write helper files for the pipeline"
    
    wd.update_utils(name=name, path=Path(f"utils/{name}.py"),
                    metadata=metadata, content=content,overwrite=overwrite)
    
    return "Updated, you can view project info to confirm"

@server.tool()
def delete_util(name:str):
    "delete a utility file"
    wd.delete_utils(name=name)
    
    return "Deleted utility file, you can view project info to confirm"




@server.tool()
def create_analysis_dashboard_item(name: str,file_content: str, capture_variables: list[str]):
    """
    create a file that produces some variable containing pandas dataframe or matplotlib 
    figure objects or list or dictionaries that will show on the dashboard.
    It only reads the variables from the file that are given in 'capture_variables' argument.
    """
    
    script_path = cwp_path / "analysis" / f"{name}.py"
    
    wd.update_analysis(name=name,path=Path(f"analysis/{name}.py"),metadata=captured,content=file_content)
    captured = capture_script_outputs(project_root=cwp_path,script_path=script_path,variables=capture_variables)
    
    
    
    


