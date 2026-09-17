"""
AARKAAI Production Operational Tooling – Automated Rollback Engine (Gate 3).

Features:
- Instant circuit breaker and safe fallback degradation.
- Automatic trigger upon CRITICAL alerts (HighErrorRate, SecurityAnomalyDetected).
- Explicit operator rearm workflow.
- Clean container and process teardown with tamper-evident audit logging.
"""
from __future__ import annotations

import time
import shutil
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import config
from modules.security_audit import audit_event

logger = logging.getLogger("aarkaai.rollback")


@dataclass
class RollbackState:
    is_rolled_back: bool = False
    triggered_at: Optional[float] = None
    reason: Optional[str] = None
    operator: Optional[str] = None
    previous_code_mode: bool = True
    previous_mcp: bool = True


class RollbackController:
    _instance: Optional[RollbackController] = None

    def __init__(self):
        self.state = RollbackState()

    @classmethod
    def get_instance(cls) -> RollbackController:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def trigger_rollback(self, reason: str, operator: str = "automated_circuit_breaker") -> RollbackState:
        """
        Executes immediate emergency rollback:
        1. Disables Code Mode (falls back to safe read-only ReAct loop).
        2. Disables MCP Client.
        3. Force-terminates any running sandbox containers.
        4. Emits high-priority audit record.
        """
        now = time.time()
        logger.critical("EMERGENCY ROLLBACK INITIATED: %s (operator: %s)", reason, operator)

        self.state.is_rolled_back = True
        self.state.triggered_at = now
        self.state.reason = reason
        self.state.operator = operator
        self.state.previous_code_mode = config.CODE_MODE_ENABLED
        self.state.previous_mcp = config.MCP_ENABLED

        # 1. Flip runtime feature flags to safe closed state
        config.CODE_MODE_ENABLED = False
        config.MCP_ENABLED = False

        # 2. Terminate active containers if Docker is reachable
        if shutil.which("docker"):
            try:
                subprocess.run(
                    ["docker", "kill", "$(docker ps -q --filter name=aarkaa_sandbox)"],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5.0,
                    check=False
                )
            except Exception as e:
                logger.warning("Docker cleanup during rollback warning: %s", e)

        # 3. Disconnect MCP clients if active
        try:
            from modules.tools import get_mcp_client
            client = get_mcp_client()
            if client:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(client.shutdown())
                    else:
                        loop.run_until_complete(client.shutdown())
                except Exception:
                    pass
        except Exception as e:
            logger.warning("MCP shutdown during rollback warning: %s", e)

        # 4. Audit event
        audit_event(
            "rollback.triggered",
            reason=reason,
            operator=operator,
            code_mode_enabled=False,
            mcp_enabled=False,
            is_production=config.IS_PRODUCTION
        )

        return self.state

    def rearm_staging(self, operator: str = "admin_operator") -> RollbackState:
        """Restores controlled staging operational configuration."""
        logger.info("Rearming Controlled Staging configuration (operator: %s)", operator)
        self.state.is_rolled_back = False
        self.state.triggered_at = None
        self.state.reason = None
        self.state.operator = operator

        config.CODE_MODE_ENABLED = True
        config.MCP_ENABLED = True
        config.IS_PRODUCTION = False

        audit_event(
            "rollback.rearmed",
            operator=operator,
            code_mode_enabled=True,
            mcp_enabled=True,
            is_production=False
        )
        return self.state

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_rolled_back": self.state.is_rolled_back,
            "triggered_at": self.state.triggered_at,
            "reason": self.state.reason,
            "operator": self.state.operator,
            "runtime_flags": {
                "CODE_MODE_ENABLED": config.CODE_MODE_ENABLED,
                "MCP_ENABLED": config.MCP_ENABLED,
                "IS_PRODUCTION": config.IS_PRODUCTION
            }
        }


# Global singleton
rollback_controller = RollbackController()
