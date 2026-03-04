from flask import Flask, request, jsonify, send_file, render_template
from pathlib import Path
import json

from dist_automl.dashboard_maker.dashboard_capture import capture_script_outputs


PROJECT_FILE = (Path(__file__).parent.parent / "managers" / "current_project_root.txt")


def get_current_project():

    if not PROJECT_FILE.exists():
        raise RuntimeError("No project is set as working, use 'set' command to set a working project")

    project_root = PROJECT_FILE.read_text().strip()

    return Path(project_root).resolve()

app = Flask(__name__, template_folder=Path(__file__).parent / "templates", static_folder=Path(__file__).parent / "static")

def load_metadata(project_root):

    meta_file = Path(project_root) / "dashboard_runs" / "metadata.json"

    if not meta_file.exists():
        return {}

    with open(meta_file) as f:
        return json.load(f)
    
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run-script", methods=["POST"])
def run_script():

    data = request.json

    project_root = get_current_project()
    script_path = data["script_path"]

    outputs = capture_script_outputs(project_root, script_path)

    return jsonify(outputs)

@app.route("/variables")
def get_variables():

    project_root = get_current_project()

    metadata = load_metadata(project_root)

    return jsonify(metadata)

@app.route("/data")
def get_data():

    project_root = get_current_project()
    file_path = request.args.get("file_path")

    base = Path(project_root) / "dashboard_runs"
    path = base / file_path

    if not path.exists():
        return jsonify({"error": "file not found"}), 404

    if path.suffix == ".png":
        return send_file(path)

    return jsonify(json.loads(path.read_text()))

@app.route("/refresh", methods=["POST"])
def refresh():

    data = request.json

    project_root = get_current_project()
    script_path = data["script_path"]

    outputs = capture_script_outputs(project_root, script_path)

    return jsonify(outputs)

if __name__ == "__main__":
    app.run(debug=True)