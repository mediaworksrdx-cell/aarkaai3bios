"""
AARKAAI – Supervisor
Monates agent state, execution windows, loops, retry limits, and timeout protection.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Supervisor:
    """Supervisor monitors DAG execution logs streamingly to prevent infinite tool loops."""
    
    def __init__(self, global_retry_limit: int = 5, global_timeout_seconds: float = 120.0):
        self.global_retry_limit = global_retry_limit
        self.global_timeout_seconds = global_timeout_seconds
        
        # Monitor execution statistics
        self.total_retries = 0
        self.execution_history: List[Dict[str, Any]] = []

    def check_loop(self, task_id: str, tool_name: str, params: Dict[str, Any]) -> bool:
        """Analyze sliding window of recent actions for consecutive identical requests."""
        # Record this invocation
        record = {
            "task_id": task_id,
            "tool_name": tool_name,
            "params_hash": hash(json.dumps(params, sort_keys=True))
        }
        self.execution_history.append(record)
        
        # Enforce sliding window loop checking
        window_size = 4
        if len(self.execution_history) >= window_size:
            recent = self.execution_history[-window_size:]
            # Check if all tools and arguments in window are identical
            first = recent[0]
            if all(r["tool_name"] == first["tool_name"] and r["params_hash"] == first["params_hash"] for r in recent):
                logger.warning("SUPERVISOR: Infinite execution loop detected on tool %s!", tool_name)
                return True
        return False

    def check_retry_budget(self) -> bool:
        """Check if global retry budget across entire execution DAG has been exhausted."""
        if self.total_retries >= self.global_retry_limit:
            logger.error("SUPERVISOR: Global retry budget (%d) exceeded!", self.global_retry_limit)
            return False
        return True

    def record_retry(self):
        self.total_retries += 1
