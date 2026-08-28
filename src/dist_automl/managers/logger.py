import logging
import json
import time
import functools
from pathlib import Path
from typing import Any, Optional

def get_project_logger(project_root: Optional[Path] = None):
    """
    Returns a ProjectLogger instance for the given project_root.
    If project_root is None, attempts to resolve it using projects_manager.
    """
    if project_root is None:
        from dist_automl.managers.projects_manager import ProjectJSON
        config = ProjectJSON()
        cwp_name = config.get_cwp()
        if cwp_name:
            for p in config.list_projects():
                if p.name == cwp_name:
                    project_root = p.root
                    break
    
    if project_root and project_root.exists():
        return ProjectLogger(project_root)
    return None

class ProjectLogger:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.log_file = project_root / "automl.log"
        self.logger = logging.getLogger(f"automl_project_{project_root.resolve().as_posix()}")
        self.logger.setLevel(logging.INFO)
        
        # Prevent adding multiple handlers if instantiated multiple times
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter('[%(asctime)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _format_event(self, source: str, level: str, event: str, duration_ms: float, details: dict) -> str:
        duration_str = f"[{duration_ms:.2f}ms]" if duration_ms > 0 else "[]"
        details_str = json.dumps(details, default=str)
        return f"[{source}] [{level}] [{event}] {duration_str} {details_str}"

    def log_tool_call(self, tool_name: str, args: dict, result: Any = None, error: Exception = None, duration_ms: float = 0):
        details = {"args": args}
        if error:
            details["error"] = str(error)
            level = "ERROR"
        else:
            if result is not None:
                details["result"] = str(result)[:500]  # truncate long results
            level = "INFO"
        
        msg = self._format_event("MCP", level, f"TOOL:{tool_name}", duration_ms, details)
        self.logger.info(msg)

    def log_cli_command(self, command: str, args: dict, exit_code: int = 0, error: Exception = None, duration_ms: float = 0):
        details = {"args": args, "exit_code": exit_code}
        if error:
            details["error"] = str(error)
            level = "ERROR"
        else:
            level = "INFO"
        
        msg = self._format_event("CLI", level, f"CMD:{command}", duration_ms, details)
        self.logger.info(msg)

def logged_tool(func):
    """
    Decorator for FastMCP tool functions to automatically log their execution.
    It resolves the project root internally.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start_time) * 1000
            logger = get_project_logger()
            if logger:
                call_args = kwargs.copy()
                if args:
                    call_args["_args"] = args
                logger.log_tool_call(func.__name__, call_args, result=result, duration_ms=duration)
            return result
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger = get_project_logger()
            if logger:
                call_args = kwargs.copy()
                if args:
                    call_args["_args"] = args
                logger.log_tool_call(func.__name__, call_args, error=e, duration_ms=duration)
            raise
    return wrapper
