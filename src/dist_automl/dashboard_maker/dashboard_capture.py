import json
import runpy
from pathlib import Path

from dist_automl.dashboard_maker.serializer import (
    serialize_dataframe,
    serialize_list,
    serialize_dict,
    serialize_number,
    serialize_figure
)

from dist_automl.dashboard_maker.type_detector import detect_type


def capture_script_outputs(project_root, script_path, variables):

    project_root = Path(project_root)
    script_path = Path(script_path)

    base = project_root / "dashboard_runs"
    data_dir = base / "data"
    img_dir = base / "images"
    meta_file = base / "metadata.json"

    data_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    namespace = runpy.run_path(script_path)

    if meta_file.exists():
        metadata = json.loads(meta_file.read_text())
    else:
        metadata = {"scripts": {}}

    script_key = str(script_path)

    metadata["scripts"].setdefault(script_key, {})

    for name, obj in namespace.items():

        if name not in variables:
            continue

        obj_type = detect_type(obj)

        if obj_type is None:
            continue

        if obj_type == "dataframe":

            path = data_dir / f"{script_path.stem}_{name}.json"
            serialize_dataframe(obj, path)

        elif obj_type == "figure":

            path = img_dir / f"{script_path.stem}_{name}.png"
            serialize_figure(obj, path)

        elif obj_type == "list":

            path = data_dir / f"{script_path.stem}_{name}.json"
            serialize_list(obj, path)

        elif obj_type == "dict":

            path = data_dir / f"{script_path.stem}_{name}.json"
            serialize_dict(obj, path)

        elif obj_type == "kpi":

            path = data_dir / f"{script_path.stem}_{name}.json"
            serialize_number(obj, path)

        metadata["scripts"][script_key][name] = {
            "type": obj_type,
            "path": str(path.relative_to(base))
        }

    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata["scripts"][script_key]



# from dashboard_capture import capture_script_outputs

# capture_script_outputs(
#     project_root="my_project",
#     script_path="scripts/train.py"
# )