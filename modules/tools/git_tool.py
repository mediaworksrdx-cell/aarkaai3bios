import os
import re
import shlex
import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

# Allowlist of permitted git subcommands. Any subcommand not in this set is blocked.
GIT_ALLOWED_SUBCOMMANDS = {
    "status", "diff", "log", "branch", "show", "fetch",
    "clone", "checkout", "add", "commit", "stash", "tag",
    "remote", "pull", "config",
}

# Subcommands that are always blocked regardless of allowlist
GIT_BLOCKED_SUBCOMMANDS = {"push", "reset", "clean", "gc", "reflog", "filter-branch", "filter-repo"}


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
            # Strip AuthParams suffix before parsing (handled separately below)
            clean_cmd = re.sub(r'\[AuthParams:[^\]]+\]', '', raw_command).strip()
            # Use shlex.split for correct tokenization (handles quoted arguments)
            try:
                cmd_parts = shlex.split(clean_cmd)
            except ValueError as parse_err:
                return f"Error: Failed to parse git command: {parse_err}"

            # Strip leading 'git' token if present
            if cmd_parts and cmd_parts[0].lower() == "git":
                cmd_parts = cmd_parts[1:]

            if not cmd_parts:
                return "Error: Empty git subcommand."

            # Position-aware, case-insensitive subcommand check
            subcmd = cmd_parts[0].lower()
            if subcmd in GIT_BLOCKED_SUBCOMMANDS:
                return f"Error: Git subcommand '{subcmd}' is not permitted for security reasons."
            if subcmd not in GIT_ALLOWED_SUBCOMMANDS:
                return f"Error: Git subcommand '{subcmd}' is not in the permitted list: {sorted(GIT_ALLOWED_SUBCOMMANDS)}"

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
            user_match = re.search(r'username="([^"]+)"', raw_command)
            token_match = re.search(r'token="([^"]+)"', raw_command)
            if user_match:
                credentials_username = user_match.group(1)
            if token_match:
                credentials_token = token_match.group(1)
            
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
                # Write credentials to a temporary .git-credentials file instead of
                # using a shell function literal (which allows shell injection via
                # unvalidated username/token values).
                import urllib.parse
                safe_username = urllib.parse.quote(str(credentials_username), safe="")
                safe_token = urllib.parse.quote(str(credentials_token), safe="")
                creds_content = f"https://{safe_username}:{safe_token}@github.com\n"
                creds_path = SAFE_WORK_DIR / ".git-credentials"
                try:
                    creds_path.write_text(creds_content, encoding="utf-8")
                    creds_path.chmod(0o600)
                except Exception as e:
                    return f"Failed writing credentials file: {e}"
                # Configure git to use the store helper pointing to the file
                config_args = ["git", "config", "credential.helper", f"store --file={creds_path}"]
                try:
                    subprocess.run(config_args, cwd=str(SAFE_WORK_DIR), env=env, check=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                except Exception as e:
                    return f"Failed configuring credentials: {e}"

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
