# Agent Best Practices

> This file is automatically created when a project is initialized with AutoML MCP.  
> You can edit it to customize the agent's behavior for this specific project.

## Getting Started

1. **Read project info first.** Always call `get_current_project_info` at the start of a session to understand the current state of the project — what datasets are registered, which pipeline stages exist, and what utilities are available.

2. **Plan before coding.** Use `manage_plan` to write your approach in `agentplan.md` and present it to the user for approval before making file changes.

## File Writing Guidelines

- **Pipeline files** should be modular and reusable. Use `sys.argv` to accept command-line arguments so files can be run independently or composed together.
- **Utility files** are shared helpers — keep them focused and well-documented so pipeline stages can import from them.
- **Use `depends_on`** when writing pipeline elements to declare which other elements or utils they rely on. This keeps the dependency graph explicit.
- **Don't overwrite without asking.** If a file already exists, confirm with the user before passing `overwrite=True`.

## Analysis & Dashboard

- Analysis scripts capture variables (DataFrames, plots, dicts, lists) to the dashboard automatically.
- Write self-contained analysis scripts — they run in a subprocess, so they must import everything they need.
- Use `read_dashboard_items` to review previously captured data before creating new analysis.

## Project Structure

```
project_root/
├── config.yaml          # Project configuration (managed automatically)
├── agent.md             # This file — agent instructions
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
