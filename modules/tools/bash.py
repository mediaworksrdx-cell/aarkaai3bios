"""
AARKAAI – BashTool (Allowlist Architecture)

Executes shell commands inside a sandboxed workspace directory.
Uses an allowlist of permitted base commands instead of a blocklist.

Security layers:
1. Allowlist: Only explicitly permitted commands can run
2. Dangerous pattern regex: Blocks shell injection patterns regardless of allowlist
3. Python AST check: Validates referenced Python scripts (via execution_engine)
4. Workspace isolation: Commands run inside SAFE_WORK_DIR only
5. Timeout: Hard 30-second default timeout on all executions
"""
import logging
import os
import re
import shlex
import subprocess
import sys
from typing import Any, Dict, Tuple

from config import BASH_TIMEOUT, SAFE_WORK_DIR
from modules.tools.base import Tool

logger = logging.getLogger(__name__)

# ─── Allowlist: Only these base commands are permitted ────────────────────────
ALLOWED_COMMANDS = {
    # Python
    "python", "python3", "pip", "pip3",
    # Node.js
    "node", "npm", "npx",
    # Read-only file inspection
    "cat", "head", "tail", "wc", "grep", "find", "ls", "pwd", "echo",
    "sort", "uniq", "tr", "cut", "awk", "sed",
    "file", "stat", "du", "df", "tree",
    # Version control
    "git", "diff",
    # Network (read-only)
    "curl", "wget",
    # Dev tools
    "pytest", "ruff", "mypy", "black", "flake8", "isort",
    "make", "cmake",
    # Directory operations
    "mkdir", "touch", "cp", "mv",
}

# ─── Dangerous patterns: ALWAYS blocked regardless of allowlist ───────────
ALWAYS_BLOCKED_PATTERNS = [
    r'\|\s*(?:bash|sh|zsh|dash|csh|ksh)\b',  # pipe to shell
    r'[`]',                                      # backtick command substitution
    r'\$\(',                                    # $() command substitution
    r'\beval\b',                                 # eval
    r'\bexec\b',                                 # exec
    r'\bsudo\b',                                 # privilege escalation
    r'\bsu\b\s',                                # switch user
    r'\brm\s+(-[rRf]+\s+)?/',                  # rm from root
    r'\brm\s+-[rRf]*\s',                        # any rm -rf
    r'\bchmod\b.*\b777\b',                      # world-writable
    r'\bchown\b',                                # ownership change
    r'\bmkfs\b',                                 # format disk
    r'\bdd\s+if=',                               # disk write
    r'>\s*/dev/',                                 # write to devices
    r'\bshutdown\b',                             # shutdown
    r'\breboot\b',                               # reboot
    r'\bpoweroff\b',                             # poweroff
    r'\bsystemctl\b',                            # service management
    r'\bkill\b\s+-9',                           # force kill
    r'\bkillall\b',                              # kill all processes
    r'\bnc\b.*-[le]',                            # netcat listen
    r'\btelnet\b',                               # telnet
    r'\bssh\b',                                  # ssh
    r'\bscp\b',                                  # scp
    r':\(\)\{',                                  # fork bomb
    r'/etc/(?:passwd|shadow|sudoers)',            # sensitive system files
    r'\bwget\b.*-O\s*-\s*\|',                  # wget pipe to shell
    r'\bcurl\b.*\|\s*(?:bash|sh)',              # curl pipe to shell
]


def _validate_command(command: str) -> Tuple[bool, str]:
    """Validate command against allowlist and dangerous pattern checks.
    
    Returns:
        (is_valid, reason) tuple.
    """
    if not command or not command.strip():
        return False, "Empty command"
    
    # Step 1: Check dangerous patterns (always blocked)
    for pattern in ALWAYS_BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Blocked: matches dangerous pattern"
    
    # Step 2: Extract base command and validate against allowlist
    # Handle compound commands (&&, ||, ;) by checking each part
    # Split on shell operators
    parts = re.split(r'\s*(?:&&|\|\||;)\s*', command.strip())
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Handle environment variable prefixes (e.g., "VAR=val command")
        while '=' in part.split()[0] if part.split() else False:
            part = ' '.join(part.split()[1:])
            if not part:
                break
        
        if not part:
            continue
        
        # Extract the base command name
        try:
            tokens = shlex.split(part)
        except ValueError:
            return False, "Blocked: malformed command (unmatched quotes)"
        
        if not tokens:
            continue
        
        base_cmd = tokens[0].split("/")[-1]  # /usr/bin/python -> python
        
        # Strip version suffixes (python3.11 -> python3)
        base_cmd_normalized = re.sub(r'(\d+\.\d+)$', '', base_cmd)
        
        if base_cmd not in ALLOWED_COMMANDS and base_cmd_normalized not in ALLOWED_COMMANDS:
            return False, f"Blocked: '{base_cmd}' is not in the allowed commands list"
    
    return True, "Allowed"


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

    def execute(self, params: Dict[str, Any]) -> str:
        cmd = params.get("command")
        if not cmd:
            return "Error: 'command' argument is required."

        # Validate against allowlist + dangerous patterns
        is_valid, reason = _validate_command(cmd)
        if not is_valid:
            logger.warning("BLOCKED command (%s): %s", reason, cmd[:120])
            return f"Error: This command is not allowed for security reasons. {reason}"

        work_dir = SAFE_WORK_DIR
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Normalize python/pip paths to current interpreter
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
            sub_env["PAGER"] = "cat"

            # SEC-C2 FIX: Use shell=False with shlex.split() to prevent
            # shell metacharacter injection. The allowlist validation above
            # ensures only permitted base commands reach this point, and
            # shell=False prevents any remaining injection vectors.
            try:
                # Use posix=False on Windows to preserve file path backslashes
                cmd_args = shlex.split(cmd_normalized, posix=(os.name != "nt"))
                if os.name == "nt":
                    cmd_args = [
                        arg[1:-1] if (len(arg) >= 2 and arg.startswith("'") and arg.endswith("'")) else arg
                        for arg in cmd_args
                    ]
            except ValueError as parse_err:
                return f"Error: Failed to parse command: {parse_err}"

            result = subprocess.run(
                cmd_args,
                shell=False,
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
