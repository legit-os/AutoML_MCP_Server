from pathlib import Path
import subprocess
import sys
import json
import platform
import tempfile


def get_venv_python(project_root: Path, venv_path: str):

    venv = project_root / venv_path

    if platform.system() == "Windows":
        return venv / "Scripts" / "python.exe"

    return venv / "bin" / "python"



def get_dashboard_paths(project_root: Path):

    base = project_root / "dashboard_runs"

    paths = {
        "base": base,
        "data": base / "data",
        "images": base / "images",
        "meta": base / "metadata.json"
    }

    for p in paths.values():
        if isinstance(p, Path) and p.suffix == "":
            p.mkdir(parents=True, exist_ok=True)

    return paths



def load_metadata(meta_file):

    if meta_file.exists():
        return json.loads(meta_file.read_text())

    return {"scripts": {}}


def save_metadata(meta_file, data):

    with open(meta_file, "w") as f:
        json.dump(data, f, indent=2)
        
def create_wrapper(script_path, output_json):

    wrapper = f"""
import runpy
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from pathlib import Path

namespace = runpy.run_path("{script_path}")

results = {{}}

for k,v in namespace.items():

    if k.startswith("__"):
        continue

    t = type(v).__name__

    if isinstance(v, (int,float)):
        results[k] = {{"type":"number"}}

    elif isinstance(v, list):
        results[k] = {{"type":"list"}}

    elif isinstance(v, dict):
        results[k] = {{"type":"dict"}}

    elif isinstance(v, pd.DataFrame):
        results[k] = {{"type":"dataframe"}}

    elif isinstance(v, Figure):
        results[k] = {{"type":"figure"}}

Path("{output_json}").write_text(json.dumps(results))
"""

    return wrapper





def run_script_capture(project_root, script_path, venv_path=".venv"):

    project_root = Path(project_root)
    script_path = Path(script_path)

    paths = get_dashboard_paths(project_root)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        wrapper_path = Path(f.name)

    output_json = wrapper_path.with_suffix(".json")

    wrapper_code = create_wrapper(script_path, output_json)

    wrapper_path.write_text(wrapper_code)

    python_exec = get_venv_python(project_root, venv_path)

    subprocess.run(
        [str(python_exec), str(wrapper_path)],
        cwd=project_root
    )

    results = json.loads(output_json.read_text())

    return results