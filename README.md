# AutoML MCP

![Python](https://img.shields.io/badge/Python-3.14%2B-blue)
![FastMCP](https://img.shields.io/badge/FastMCP-Supported-green)
![Typer](https://img.shields.io/badge/Typer-CLI-black)
![FastAPI](https://img.shields.io/badge/FastAPI-Dashboard-teal)
![React](https://img.shields.io/badge/React-Frontend-blue)
![uv](https://img.shields.io/badge/uv-Package_Manager-purple)

## What is AutoML MCP?

AutoML MCP is a specialized toolkit designed to empower AI assistants (Agents) to execute end-to-end Machine Learning projects in a **deterministic and structured way**. 

By providing a Model Context Protocol (MCP) server alongside a dedicated CLI, it gives AI agents the exact utilities they need to handle the entire ML lifecycle—from initial exploratory data analysis to model training and deployment.

**What it IS:**
- A bridge that gives AI agents structured file management, Jupyter notebook manipulation, and dashboard creation capabilities.
- A standardized workflow enforcer for ML projects created by AI.
- A toolset that allows agents to safely register datasets, manage pipeline stages, and visualize data.

**What it IS NOT:**
- It is **not** a version control system like Git.
- It is **not** a general project or package manager like `uv` or `poetry` (It manages the files and items created by agent or given by the user required in the Machine Learning Workflow).

---

## Installation & Usage

### Prerequisites
Make sure you have [uv](https://docs.astral.sh/uv/) installed.
For background task support, you must also have [PM2](https://pm2.keymetrics.io/) installed globally via npm (`npm install -g pm2`).

### Installation

Using uv tools:
```bash
uv tool install git+https://github.com/legit-os/AutoML_MCP_Server.git -U
```

### Basic Workflow
1. **Initialize a new ML project directory**:
   ```bash
   automl init ./my_ml_project -n MyProject
   ```
2. **Start the MCP Server** (so your AI agent can connect):
   ```bash
   automl mcp start
   ```
   *(To get the config JSON to paste into your MCP client, run `automl mcp`)*
3. **Launch the Dashboard** (to view agent-generated visualizations):
   ```bash
   automl dashboard
   ```

---

## What We Offer

### 1. The `automl` CLI
The CLI is used by the human user to manage projects and track state. Key commands include:

| Command | Description |
|---------|-------------|
| `automl init <dir>` | Initializes a directory for tracking and creates the base folder structure. |
| `automl set <name>` | Sets the active working project for the MCP server. |
| `automl get` | Shows the currently active project. |
| `automl dashboard` | Launches the React/FastAPI dashboard to view visualizations. |
| `automl mcp` | Prints the JSON configuration for your MCP client. |
| `automl mcp start` | Starts the FastMCP server over HTTP. |
| `automl track <type>` | Manually syncs or registers existing files into the project configuration. |

### 2. The MCP Server Tools
The MCP Server exposes these tools directly to the AI agent, allowing it to manipulate the project dynamically. 
More than 20 tools are exposed in this mcp server, ensure your agent has enough context and your llm is trained to pick correct tool from too many tool options.
If you use a agent that uses an extra tool calling agent or dedicated tool like the agent of antigravity, then it is OK.


| Tool Name | Description |
|-----------|-------------|
| `get_current_project_info` | Reads the project configuration, showing active datasets, files, and paths. |
| `manage_plan` | Reads or writes to `agentplan.md` to establish a plan before coding. |
| `write_pipeline_element` | Creates modular `.py` files for specific ML pipeline stages (e.g., preprocessing, training). |
| `write_util` | Creates utility scripts for the pipeline. |
| `manage_notebook` | Reads, adds, edits, or deletes specific cells in Jupyter Notebooks (`.ipynb`). |
| `list_notebooks` | Lists all notebooks currently in the project. |
| `register_dataset` / `delete_dataset` | Tracks or removes dataset references in the project config. |
| `manage_ops_file` | Writes infrastructure files (Dockerfiles, DVC configs, etc.). |
| `create_analysis_dashboard_item` | Writes an analysis script and automatically captures selected variables (DataFrames, plots) to the dashboard. |
| `read_dashboard_items` | Allows the agent to read back the data (lists, dicts, DataFrames) it previously plotted on the dashboard. |
| `update_project_metadata` | Updates global project metadata (author, version, etc.). |
| `run_background_task` | Launches a terminal command or script securely via PM2. Supports both blocking and non-blocking background execution. |
| `manage_background_task` | Stops, deletes, or checks the status and logs of a running PM2 task. |


This server doesn't have a generic synchronous tool to run foreground CLI commands since many agents restrict that behaviour; you may need to use your agent provider's native MCP server for running short commands (like antigravity and claude can run commands from their own capabilities). However, the background task tools provided above allow safe, asynchronous execution of long-running operations.