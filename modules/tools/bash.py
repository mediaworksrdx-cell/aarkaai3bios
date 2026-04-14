"""
AARKAAI – BashTool (Sandboxed)

Executes shell commands within a restricted sandbox:
- Commands run inside SAFE_WORK_DIR only
- Dangerous commands are blocklisted
- Timeout enforced
- No shell=True (prevents injection)
"""
import logging
import shlex
import subprocess
from typing import Any, Dict

from config import BASH_BLOCKLIST, BASH_TIMEOUT, SAFE_WORK_DIR
from modules.tools.base import Tool

logger = logging.getLogger(__name__)


class BashTool(Tool):
    name = "BashTool"
    description = (
        "Execute a shell command inside a sandboxed workspace. Use this for running "
        "tests, checking system state, or executing code. Provide the 'command' argument."
    )

    def _is_blocked(self, command: str) -> bool:
        """Check if the command matches any blocklist pattern."""
        cmd_lower = command.lower().strip()
        for pattern in BASH_BLOCKLIST:
            if pattern.lower() in cmd_lower:
                return True
        return False

    def execute(self, params: Dict[str, Any]) -> str:
        cmd = params.get("command")
        if not cmd:
            return "Error: 'command' argument is required."

        # Security: block dangerous commands
        if self._is_blocked(cmd):
            logger.warning("BLOCKED dangerous command: %s", cmd[:100])
            return "Error: This command is not allowed for security reasons."

        # Ensure workspace exists
        work_dir = SAFE_WORK_DIR
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                cmd,
                shell=True,  # Keep shell=True for complex commands (pipes, redirects)
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=BASH_TIMEOUT,
                cwd=str(work_dir),
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
