---
name: automl-workflow
description: Guidelines, best practices, and instructions for managing end-to-end Machine Learning workflows, planning, pipeline stages, utilities, dashboards, and background tasks using AutoML MCP.
---

# AutoML MCP Workflow & Guidelines

> This skill provides instructions and best practices for managing machine learning projects with AutoML MCP.

## Getting Started

1. **Read project info first.** Always call `get_current_project_info` at the start of a session to understand the current state of the project — what datasets are registered, which pipeline stages exist, and what utilities are available.

2. **Plan before coding.** Use `manage_plan` to write your approach in `agentplan.md` and present it to the user for approval before making file changes.

## File Writing Guidelines

- **Flexible File Structures**: You can create arbitrary file structures and use custom extensions (like `.txt`, `.json`, tests, etc.) by passing the optional `file_path` argument to `write_pipeline_element` and `write_util`. If omitted, they default to the `pipeline/` and `utils/` directories.
- **Editing Files directly:** The `edit_file` tool lets you read and write to specific line ranges (or overwrite/create entire untracked files like `.txt`, tests, config files) without altering the project's tracked config schema. Use this when you don't need the file to be a registered ML component.
- **Pipeline files** should be modular and reusable. Use `sys.argv` to accept command-line arguments so files can be run independently or composed together.
- **Utility files** are shared helpers — keep them focused and well-documented so pipeline stages can import from them.
- **Use `depends_on`** when writing pipeline elements to declare which other elements or utils they rely on. This keeps the dependency graph explicit.
- **Updating dependencies without rewriting:** To update an element's `depends_on` metadata without changing its code, call `write_pipeline_element` with `overwrite=True` and omit the `content` argument (or pass `null`/`None`). This saves tokens and avoids overwriting the file.
- **Don't overwrite without asking.** If a file already exists, confirm with the user before passing `overwrite=True` (unless you are only updating metadata as described above).

## Analysis & Dashboard

- Analysis scripts capture variables (DataFrames, plots, dicts, lists) to the dashboard automatically.
- Write self-contained analysis scripts — they run in a subprocess, so they must import everything they need.
- Use `read_dashboard_items` to review previously captured data before creating new analysis.

## Background Tasks & Processes

- **Long-Running Commands:** If you need to execute a long-running process (e.g., model training, data scraping), use `run_background_task` to spawn it via PM2. You can optionally specify a `cwd` to run the command in a specific directory (defaults to the active project root). 
- **Execution Modes:** Use `background=True` (default) to start the task and return immediately (non-blocking). Note: You will NOT be notified when the task completes. Use `background=False` if you need to block and wait for the task to finish before proceeding (the tool will wait and return the final status and logs).
- **Task Management:** Use `manage_background_task` to fetch logs (`action="logs"`) or check if a task is "online" or "stopped" (`action="status"`). Clean up tasks when they are no longer needed (`action="delete"`).

## Project Structure

```
project_root/
├── config.yaml          # Project configuration (managed automatically)
├── .agents/skills/      # Agent skills (e.g., this SKILL.md file)
├── automl.log           # Logs for MCP tool calls and CLI commands
├── agentplan.md         # Agent's working plan (created via manage_plan)
├── pipeline/            # ML pipeline stage files
├── utils/               # Shared utility modules
├── analysis/            # Analysis scripts for dashboard
└── dashboard_runs/      # Auto-generated dashboard data (gitignored)
```

## Conventions

- Keep file names descriptive and lowercase with underscores (e.g., `feature_engineering.py`).
- One responsibility per pipeline file — split large stages into focused elements.
- Document any assumptions about the dataset in the file's docstring.
- If creating infrastructure files (Dockerfile, docker-compose, CI configs), use `manage_ops_file` with `track=True` so they appear in the project config.
