from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import json
import os
from pydantic import BaseModel
from typing import Dict, Any

from dist_automl.managers.projects_manager import ProjectJSON

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/_event/")
async def websocket_endpoint(websocket: WebSocket):
    """Catch-all for 'ghost' Reflex connections to prevent server errors."""
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

def get_project_root() -> Path:
    pj = ProjectJSON()
    # Path to current_project_root.txt
    root_file = Path(pj.path_to_cwd)
    if not root_file.exists():
        raise HTTPException(status_code=404, detail="No project initialized or selected.")
    return Path(root_file.read_text().strip())

@app.get("/api/metadata")
async def get_metadata():
    try:
        root = get_project_root()
        meta_path = root / "dashboard_runs" / "metadata.json"
        if not meta_path.exists():
            return {"scripts": {}}
        return json.loads(meta_path.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data")
async def get_data(path: str):
    try:
        root = get_project_root()
        data_path = (root / "dashboard_runs" / path).resolve()
        
        # Security check: ensure path is within dashboard_runs
        if not str(data_path).startswith(str((root / "dashboard_runs").resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
            
        if not data_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        return json.loads(data_path.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image")
async def get_image(path: str):
    try:
        root = get_project_root()
        img_path = (root / "dashboard_runs" / path).resolve()
        
        if not str(img_path).startswith(str((root / "dashboard_runs").resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
            
        if not img_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
            
        return FileResponse(img_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LayoutUpdate(BaseModel):
    script_key: str
    var_name: str
    x: float
    y: float
    width: float
    height: float

@app.post("/api/update_layout")
async def update_layout(update: LayoutUpdate):
    try:
        root = get_project_root()
        meta_path = root / "dashboard_runs" / "metadata.json"
        
        if not meta_path.exists():
            raise HTTPException(status_code=404, detail="metadata.json not found")
            
        data = json.loads(meta_path.read_text())
        scripts = data.get("scripts", {})
        
        if update.script_key in scripts and update.var_name in scripts[update.script_key]:
            var_data = scripts[update.script_key][update.var_name]
            var_data["x"] = update.x
            var_data["y"] = update.y
            var_data["width"] = update.width
            var_data["height"] = update.height
            
            meta_path.write_text(json.dumps(data, indent=4))
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Variable not found in metadata")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files from the build directory
static_dir = (Path(__file__).parent / "frontend" / "out").resolve()

if static_dir.exists():
    # Explicitly serve index.html for the root route
    @app.get("/")
    async def serve_index():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="index.html not found in static directory")

    # Mount the rest of the static files (assets, etc.)
    app.mount("/", StaticFiles(directory=str(static_dir)), name="static")
else:
    print(f"Warning: Static directory not found at {static_dir}. Frontend will not be served.")
    @app.get("/")
    async def root_warning():
        return {"message": "Dashboard server is running, but frontend assets were not found.", "path_expected": str(static_dir)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
