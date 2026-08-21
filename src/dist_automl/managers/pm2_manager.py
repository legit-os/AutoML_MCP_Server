import subprocess
import json
from typing import Dict, Any, Optional

class PM2Manager:
    @staticmethod
    def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
        try:
            # shell=True helps on Windows to resolve npm global packages like 'pm2'
            return subprocess.run(cmd, capture_output=True, text=True, shell=True)
        except Exception as e:
            raise RuntimeError(f"Failed to execute PM2 command: {e}")

    @staticmethod
    def check_installed() -> bool:
        res = PM2Manager._run_cmd(["pm2", "--version"])
        return res.returncode == 0

    @staticmethod
    def start(command: str, name: str) -> str:
        if not PM2Manager.check_installed():
            return "Error: PM2 is not installed. Please install it globally via 'npm install -g pm2'."
        
        # In pm2, to run a command with arguments as a script, we can pass it as a string
        res = PM2Manager._run_cmd(["pm2", "start", command, "--name", name])
        if res.returncode != 0:
            return f"Failed to start task '{name}': {res.stderr.strip()}"
        return f"Successfully started task '{name}' in background."

    @staticmethod
    def stop(name: str) -> str:
        res = PM2Manager._run_cmd(["pm2", "stop", name])
        if res.returncode != 0:
            return f"Failed to stop task '{name}': {res.stderr.strip()}"
        return f"Successfully stopped task '{name}'."

    @staticmethod
    def delete(name: str) -> str:
        res = PM2Manager._run_cmd(["pm2", "delete", name])
        if res.returncode != 0:
            return f"Failed to delete task '{name}': {res.stderr.strip()}"
        return f"Successfully deleted task '{name}'."

    @staticmethod
    def logs(name: str, lines: int = 50) -> str:
        res = PM2Manager._run_cmd(["pm2", "logs", name, "--nostream", "--lines", str(lines)])
        if res.returncode != 0:
            return f"Failed to get logs for task '{name}': {res.stderr.strip()}"
        return res.stdout.strip() or res.stderr.strip()

    @staticmethod
    def status(name: str) -> Dict[str, Any]:
        res = PM2Manager._run_cmd(["pm2", "jlist"])
        if res.returncode != 0:
            return {"error": f"Failed to list pm2 processes: {res.stderr.strip()}"}
        
        try:
            processes = json.loads(res.stdout)
            for p in processes:
                if p.get("name") == name:
                    return {
                        "name": p.get("name"),
                        "status": p.get("pm2_env", {}).get("status", "unknown"),
                        "cpu": p.get("monit", {}).get("cpu", 0),
                        "memory": p.get("monit", {}).get("memory", 0),
                        "restarts": p.get("pm2_env", {}).get("restart_time", 0)
                    }
            return {"error": f"Task '{name}' not found."}
        except json.JSONDecodeError:
            return {"error": "Failed to parse pm2 jlist output."}
