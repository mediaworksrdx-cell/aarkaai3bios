"""
AARKAAI – Security Audit Logging
Logs all security decisions, tool calls, and results to a secure audit file.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from config import SAFE_WORK_DIR

logger = logging.getLogger(__name__)

AUDIT_LOG_FILE = SAFE_WORK_DIR.parent / "security_audit.jsonl"

def log_audit_event(
    user_id: str,
    session_id: str,
    tool_name: str,
    params: dict,
    permission_level: str,
    verdict: str,
    details: str = ""
):
    """
    Log a security audit event in JSONL format.
    """
    # Sanitize parameters (e.g. redact potential secrets/keys)
    sanitized_params = {}
    for k, v in params.items():
        if k in ["password", "token", "secret", "key", "auth"]:
            sanitized_params[k] = "[REDACTED]"
        else:
            # truncate long parameters
            val_str = str(v)
            if len(val_str) > 500:
                sanitized_params[k] = val_str[:500] + "... [truncated]"
            else:
                sanitized_params[k] = v

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "tool_name": tool_name,
        "parameters": sanitized_params,
        "permission_level": permission_level,
        "verdict": verdict,
        "details": details
    }

    try:
        # Create folder structure if missing
        AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        logger.error("Failed to write to security audit log: %s", e)
