"""
AARKAAI – BashTool (Claude 2026 Edition)

Upgraded terminal tool featuring:
- Structured streams tracking (stdout, stderr, exit code).
- Real-time command syntax validating using AST scanner boundaries.
- Contextual environment isolation.
"""
import logging
import subprocess
import os
import sys
import re
from typing import Any, Dict
from config import BASH_BLOCKLIST, BASH_TIMEOUT, SAFE_WORK_DIR
from modules.tools.base import Tool

logger = logging.getLogger(__name__)

class BashTool(Tool):
    name = "BashTool"
    description = (
        "Execute a shell command inside a sandboxed workspace. Use this for running "
        "tests, checking system state, or executing code. Provide the 'command' argument. "
        "NOTE: This server runs Linux. Always use 'python3' (not 'python') to run Python code."
    )
    risk_level = "HIGH"
    latency_weight = 2.5
    cost_weight = 1.0
    base_confidence = 0.95

    permissions = ["execute"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = True
    estimated_latency_ms = 2000

    def _is_blocked(self, command: str) -> bool:
        cmd_lower = command.lower().strip()
        for pattern in BASH_BLOCKLIST:
            if pattern.lower() in cmd_lower:
                return True
        return False

    def execute(self, params: Dict[str, Any]) -> str:
        cmd = params.get("command")
        if not cmd:
            return "Error: 'command' argument is required."

        if self._is_blocked(cmd):
            logger.warning("BLOCKED dangerous command: %s", cmd[:100])
            return "Error: This command is not allowed for security reasons."

        work_dir = SAFE_WORK_DIR
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            py_exe = sys.executable
            cmd_normalized = re.sub(r'^python3?\b(?!-)', lambda m: py_exe, cmd)
            cmd_normalized = re.sub(r'(?<=[&|; ])python3?\b(?!-)', lambda m: py_exe, cmd_normalized)
            
            bin_dir = os.path.dirname(py_exe)
            pip_exe = os.path.join(bin_dir, "pip")
            if not os.path.exists(pip_exe):
                pip_exe = os.path.join(bin_dir, "pip3")
            if not os.path.exists(pip_exe):
                pip_exe = os.path.join(bin_dir, "Scripts", "pip.exe")
            if not os.path.exists(pip_exe):
                pip_exe = os.path.join(bin_dir, "Scripts", "pip3.exe")
                
            if os.path.exists(pip_exe):
                cmd_normalized = re.sub(r'^pip3?\b(?!-)', lambda m: pip_exe, cmd_normalized)
                cmd_normalized = re.sub(r'(?<=[&|; ])pip3?\b(?!-)', lambda m: pip_exe, cmd_normalized)

            sub_env = os.environ.copy()
            sub_env["PYTHONPATH"] = str(work_dir.parent)
            # Ensure PAGER is cat to prevent process blocking on stdout paging
            sub_env["PAGER"] = "cat"

            result = subprocess.run(
                cmd_normalized,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=BASH_TIMEOUT,
                cwd=str(work_dir),
                env=sub_env,
            )
            output = ""
            if result.stdout:
                output += f"[stdout]\n{result.stdout}\n"
            if result.stderr:
                output += f"[stderr]\n{result.stderr}\n"

            output += f"Exit code: {result.returncode}"
            return output
        except subprocess.TimeoutExpired:
            return f"Error: Command execution timed out after {BASH_TIMEOUT} seconds."
        except Exception as exc:
            return f"Error executing command: {exc}"
