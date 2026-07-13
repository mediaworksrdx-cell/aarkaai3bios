"""
AARKAAI – Hierarchical Permission & Security Layer
Determines if tool invocations should be AUTO_ALLOW, USER_CONFIRM (interactive gate), or STRICT_BLOCK.
Also implements Git Safety Guards.
"""
import re
from typing import Dict, Any, Tuple
from config import BASH_BLOCKLIST

# Git destructive actions to guard against
GIT_DESTRUCTIVE_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\b",
    r"\bgit\s+branch\s+-D\b",
    r"\bgit\s+rebase\b",
]

class PermissionLevel:
    AUTO_ALLOW = "AUTO_ALLOW"
    USER_CONFIRM = "USER_CONFIRM"
    STRICT_BLOCK = "STRICT_BLOCK"

def is_git_destructive(command: str) -> bool:
    """Check if the command contains a destructive git operation."""
    cmd_lower = command.lower().strip()
    for pattern in GIT_DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True
    return False

def verify_permission(tool_name: str, params: Dict[str, Any]) -> Tuple[str, str]:
    """
    Verify the tool invocation parameters.
    Returns (PermissionLevel, message_or_reason).
    """
    # 1. STRICT_BLOCK Checks
    if tool_name == "BashTool":
        command = params.get("command", "")
        cmd_lower = command.lower().strip()
        
        # Check central BASH_BLOCKLIST
        for pattern in BASH_BLOCKLIST:
            if pattern.lower() in cmd_lower:
                return PermissionLevel.STRICT_BLOCK, f"Command contains blocked pattern: '{pattern}'"
                
        # Check Git destructive patterns
        if is_git_destructive(command):
            return PermissionLevel.STRICT_BLOCK, "Git destructive action blocked for safety."

        # Check command chaining and injection operators
        chaining_operators = [";", "&&", "||", "|", "$(", "`"]
        is_safe_read = False
        safe_bash_patterns = [
            r"^(git status|git diff|git log|ls|pwd|cat|grep|find|dir|echo)\b"
        ]
        if any(re.match(p, command.strip()) for p in safe_bash_patterns):
            is_safe_read = True

        if not is_safe_read:
            for op in chaining_operators:
                if op in command:
                    return PermissionLevel.STRICT_BLOCK, f"Command chaining operator '{op}' blocked in non-read path."
            
    # 2. AUTO_ALLOW Checks
    # FileReadTool and WebSearchTool are always safe.
    if tool_name in ["FileReadTool", "WebSearchTool"]:
        return PermissionLevel.AUTO_ALLOW, "Safe read operation allowed."
        
    # Check if it is a read-only BashTool command
    if tool_name == "BashTool":
        command = params.get("command", "")
        # Match typical safe, read-only commands
        safe_bash_patterns = [
            r"^(git status|git diff|git log|ls|pwd|cat|grep|find|dir|echo)\b"
        ]
        if any(re.match(p, command.strip()) for p in safe_bash_patterns):
            return PermissionLevel.AUTO_ALLOW, "Safe bash read operation allowed."

    # 3. USER_CONFIRM (Interactive Gate) Checks
    # Any write operations (like FileEditTool) or general execution (like typical scripts/tests)
    if tool_name in ["FileEditTool", "BashTool", "DeleteSkillTool", "UpdateSkillTool"]:
        return PermissionLevel.USER_CONFIRM, f"Requires user confirmation for action: {tool_name}"

    # Default fallback
    return PermissionLevel.USER_CONFIRM, "Requires verification check."
