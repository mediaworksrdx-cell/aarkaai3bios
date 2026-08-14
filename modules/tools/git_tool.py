import os
import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class GitCredentialsError(Exception):
    pass

class GitTool(Tool):
    name = "GitTool"
    description = (
        "Perform structured or raw Git operations (status, diff, log, commit, checkout, config) "
        "within the workspace. Handles custom subcommands and secure token/credential config."
    )
    risk_level = "HIGH"
    latency_weight = 1.2
    cost_weight = 0.2
    base_confidence = 0.98
    
    permissions = ["read", "write"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 400

    def execute(self, params: Dict[str, Any]) -> str:
        # Check if model passed a direct raw git command parameter
        raw_command = params.get("command")
        operation = params.get("operation")
        
        # Build git subprocess execution command array safely
        args = ["git"]
        
        if raw_command:
            # Parse raw git command string (strip leading 'git ' if present)
            cmd_parts = raw_command.strip().split()
            if cmd_parts[0].lower() == "git":
                cmd_parts = cmd_parts[1:]
            
            # Block destructive operations that could wipe the repository configuration
            blocked_args = ["clean", "reset", "push"]
            for blocked in blocked_args:
                if blocked in cmd_parts:
                    return f"Error: Git command contains blocked operation '{blocked}'."
            args.extend(cmd_parts)
            
        elif operation:
            allowed_ops = ["status", "diff", "log", "branch", "show", "config"]
            if operation not in allowed_ops:
                return f"Error: Git operation '{operation}' is not supported. Allowed: {allowed_ops}"
            args.append(operation)
            if operation == "diff":
                args.extend(["--stat", "-p"])
            elif operation == "log":
                args.extend(["-n", "10", "--oneline"])
        else:
            return "Error: Either 'command' or 'operation' argument is required."

        # Support configuring credentials in GitTool securely
        credentials_token = params.get("token")
        credentials_username = params.get("username")
        
        # Extract from raw command string if injected as a suffix (e.g. [AuthParams: username="x" token="y"])
        if raw_command and "[AuthParams:" in raw_command:
            import re
            user_match = re.search(r'username="([^"]+)"', raw_command)
            token_match = re.search(r'token="([^"]+)"', raw_command)
            if user_match:
                credentials_username = user_match.group(1)
            if token_match:
                credentials_token = token_match.group(1)
            # Strip AuthParams from raw command args
            raw_command = re.sub(r'\[AuthParams:[^\]]+\]', '', raw_command).strip()
            # Rebuild args without auth parameters
            cmd_parts = raw_command.strip().split()
            if cmd_parts[0].lower() == "git":
                cmd_parts = cmd_parts[1:]
            args = ["git"] + cmd_parts
            
        # If credentials parameters are not provided, raise GitCredentialsError to bypass registry execute wrapper
        if not credentials_username or not credentials_token:
            raise GitCredentialsError("GIT_CREDENTIALS_REQUIRED: Missing GitHub username or Personal Access Token (PAT).")
        
        env = os.environ.copy()
        if credentials_token:
            # Inject HTTP authorization header credentials env variable for git helpers
            env["GIT_ASKPASS"] = "echo"
            env["GIT_TERMINAL_PROMPT"] = "0"
            # Set credentials in standard HTTPS format: https://username:token@github.com
            # Alternatively set token helper config context:
            if credentials_username:
                args = ["git", "config", "credential.helper", f"!f() {{ echo username={credentials_username}; echo password={credentials_token}; }}; f"]
                # Configure helper block first
                try:
                    subprocess.run(args, cwd=str(SAFE_WORK_DIR), env=env, check=True)
                except Exception as e:
                    return f"Failed configuring credentials helper: {e}"

        try:
            result = subprocess.run(
                args,
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=10
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"[stderr]\n{result.stderr}"
            return output if output else "Operation completed with no output."
        except Exception as e:
            return f"Error executing git command: {e}"
