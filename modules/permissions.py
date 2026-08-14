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


# ─── Tool-Level Access Control Matrix ─────────────────────────────────────────

# Maps each core tool to its access requirements
TOOL_PERMISSIONS: Dict[str, Dict[str, Any]] = {
    # Free tier tools (basic access)
    "MarketDataTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 60,
        "description": "Live market data, prices, OHLCV"
    },
    "FinancialCalculatorTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 100,
        "description": "Financial calculations and formulas"
    },
    "MarketDateTimeTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 100,
        "description": "Market sessions and expiry dates"
    },
    "KnowledgeSearchTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 30,
        "description": "RAG knowledge base search"
    },
    "FinancialNewsTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 30,
        "description": "Financial news and regulatory updates"
    },
    "TechnicalAnalysisTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 30,
        "description": "Technical indicators and signals"
    },
    # Premium tier tools (requires subscription)
    "FinancialDataTool": {
        "tier": "premium",
        "permissions": ["read"],
        "rate_limit_per_hour": 30,
        "description": "Financial statements, ratios, earnings"
    },
    "FnOAnalyticsTool": {
        "tier": "premium",
        "permissions": ["read"],
        "rate_limit_per_hour": 20,
        "description": "Options Greeks, Max Pain, IV analysis"
    },
    "PortfolioTool": {
        "tier": "free",
        "permissions": ["read", "write"],
        "rate_limit_per_hour": 50,
        "description": "Portfolio management and risk analysis"
    },
    "FinanceCodeTool": {
        "tier": "premium",
        "permissions": ["execute"],
        "rate_limit_per_hour": 10,
        "description": "Python code execution for financial analysis"
    },
    "DocumentParserTool": {
        "tier": "premium",
        "permissions": ["read"],
        "rate_limit_per_hour": 15,
        "description": "PDF and document parsing"
    },
    "DatabaseQueryTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 40,
        "description": "User data queries (portfolio, watchlist, history)"
    },
    "NotificationTool": {
        "tier": "free",
        "permissions": ["read", "write"],
        "rate_limit_per_hour": 30,
        "description": "Alerts and market events"
    },
    "AuthPermissionTool": {
        "tier": "free",
        "permissions": ["read"],
        "rate_limit_per_hour": 20,
        "description": "User access and permission checks"
    },
}

# In-memory rate limit tracker
_rate_limit_tracker: Dict[str, Dict[str, Any]] = {}


def check_tool_access(user_id: str, tool_name: str, user_tier: str = "free") -> Dict[str, Any]:
    """Check if a user can access a specific tool based on tier and rate limits.
    
    Returns dict with:
        allowed: bool
        reason: str
        remaining_calls: int
    """
    tool_config = TOOL_PERMISSIONS.get(tool_name)
    if tool_config is None:
        # Unknown tool — allow by default (it might be a system tool)
        return {"allowed": True, "reason": "Unknown tool, default allow", "remaining_calls": -1}

    # Tier check
    required_tier = tool_config["tier"]
    if required_tier == "premium" and user_tier != "premium":
        return {
            "allowed": False,
            "reason": f"{tool_name} requires premium subscription. Upgrade to access {tool_config['description']}.",
            "remaining_calls": 0
        }

    # Rate limit check
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    rate_key = f"{user_id}:{tool_name}"
    
    tracker = _rate_limit_tracker.get(rate_key)
    hourly_limit = tool_config["rate_limit_per_hour"]
    
    if tracker is None or (now - tracker["window_start"]) > timedelta(hours=1):
        # New window
        _rate_limit_tracker[rate_key] = {
            "window_start": now,
            "count": 1
        }
        return {"allowed": True, "reason": "Access granted", "remaining_calls": hourly_limit - 1}
    
    if tracker["count"] >= hourly_limit:
        minutes_remaining = 60 - int((now - tracker["window_start"]).total_seconds() / 60)
        return {
            "allowed": False,
            "reason": f"Rate limit exceeded for {tool_name}. {hourly_limit} calls/hour. Try again in ~{minutes_remaining} minutes.",
            "remaining_calls": 0
        }
    
    tracker["count"] += 1
    remaining = hourly_limit - tracker["count"]
    return {"allowed": True, "reason": "Access granted", "remaining_calls": remaining}


def get_tool_permissions_summary(user_tier: str = "free") -> list[dict]:
    """Get a summary of all tools and their access levels for a given tier."""
    summary = []
    for tool_name, config in TOOL_PERMISSIONS.items():
        accessible = config["tier"] == "free" or user_tier == "premium"
        summary.append({
            "tool": tool_name,
            "description": config["description"],
            "tier_required": config["tier"],
            "accessible": accessible,
            "rate_limit": config["rate_limit_per_hour"],
            "permissions": config["permissions"]
        })
    return summary
