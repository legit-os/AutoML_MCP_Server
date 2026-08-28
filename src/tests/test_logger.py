import pytest
from pathlib import Path
import json

from dist_automl.managers.logger import ProjectLogger

def test_project_logger_creates_file(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    
    logger = ProjectLogger(root)
    assert logger.log_file.exists()
    assert logger.log_file.name == "automl.log"

def test_project_logger_logs_tool_call(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    
    logger = ProjectLogger(root)
    logger.log_tool_call("my_tool", {"arg1": "val1"}, result="success", duration_ms=10.5)
    
    content = logger.log_file.read_text(encoding='utf-8')
    assert "my_tool" in content
    assert "val1" in content
    assert "success" in content
    assert "[INFO]" in content

def test_project_logger_logs_cli_command(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    
    logger = ProjectLogger(root)
    logger.log_cli_command("init", {"arg": "val"}, exit_code=1, error=Exception("failed"), duration_ms=5.0)
    
    content = logger.log_file.read_text(encoding='utf-8')
    assert "init" in content
    assert "failed" in content
    assert "exit_code\": 1" in content
    assert "[ERROR]" in content
