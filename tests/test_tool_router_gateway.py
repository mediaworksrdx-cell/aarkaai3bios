"""
Unit and Integration Tests for SEC-FF-TOOLROUTER:
Unifies ToolRouterPipeline and CognitiveSubagents with ToolGateway.dispatch().

Verifies:
1. ToolRouterPipeline dispatches tools via ToolGateway.
2. Path traversal in tool intent arguments is blocked by ToolGateway.
3. USER_CONFIRM tools fail closed in autonomous pipelines without approval context.
4. USER_CONFIRM tools succeed when a valid CI approval token is provided.
5. CognitiveSubagent._invoke_tools() validates permissions and enforces autonomous fail-closed.
6. CognitiveSubagent._invoke_tools() dispatches allowed tools through ToolGateway with identity tracking.
"""
import os
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.tool_router import (
    ToolRouterPipeline,
    ToolIntent,
    ToolResult,
    PipelineResult,
)
from modules.subagents.base import CognitiveSubagent, SubagentResult
from modules.subagents.analyst import AnalystAgent
from modules.ci_nonce_store import generate_ci_token, CINonceStore


@pytest.fixture
def temp_workspace(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


# ─── 1. ToolRouterPipeline Gateway Dispatch ──────────────────────────────────

def test_tool_router_executes_through_gateway(temp_workspace):
    """Verify that ToolRouterPipeline dispatches tools through ToolGateway."""
    pipeline = ToolRouterPipeline()
    intents = [
        ToolIntent(
            tool_name="MarketDateTimeTool",
            action="market_status",
            params={"exchange": "NSE"},
            confidence=0.98
        )
    ]

    results = pipeline.execute_tools(
        intents,
        user_id="test_user",
        session_id="test_session",
        workspace_dir=str(temp_workspace),
    )

    assert len(results) == 1
    assert results[0].tool_name == "MarketDateTimeTool"
    assert results[0].is_valid is True
    assert results[0].error == ""
    assert "NSE" in results[0].data or "market" in results[0].data.lower()


# ─── 2. Universal Path Traversal Guard in Pipeline ────────────────────────────

def test_tool_router_path_traversal_blocked(temp_workspace):
    """Verify that path traversal attempts in tool intent parameters are blocked by ToolGateway."""
    pipeline = ToolRouterPipeline()
    intents = [
        ToolIntent(
            tool_name="DocumentParserTool",
            action="parse",
            params={"file_path": "../../etc/passwd"},
            confidence=0.95
        )
    ]

    results = pipeline.execute_tools(
        intents,
        user_id="test_user",
        session_id="test_session",
        workspace_dir=str(temp_workspace),
    )

    assert len(results) == 1
    assert results[0].is_valid is False
    assert "Security Gateway Blocked" in results[0].error
    assert "Path traversal detected" in results[0].error


# ─── 3. Autonomous USER_CONFIRM Fail-Closed Enforcement ───────────────────────

def test_tool_router_user_confirm_fails_closed_in_autonomous_pipeline():
    """Mutating/exec operations requiring USER_CONFIRM must fail closed in autonomous mode."""
    pipeline = ToolRouterPipeline()
    intents = [
        ToolIntent(
            tool_name="BashTool",
            action="execute",
            params={"command": "rm -rf /tmp/data"},
            confidence=0.99
        ),
        ToolIntent(
            tool_name="DeployTool",
            action="deploy",
            params={"target": "production"},
            confidence=0.95
        )
    ]

    # In autonomous mode without approval token, all USER_CONFIRM tools must be blocked
    allowed, denied = pipeline.check_permissions(
        user_id="user1",
        intents=intents,
        user_tier="enterprise",
        is_autonomous=True,
        approval_context=None,
    )

    assert len(allowed) == 0
    assert len(denied) == 2
    assert any("Autonomous pipeline blocked USER_CONFIRM" in d for d in denied)


# ─── 4. CI Token Delegation in Pipeline ───────────────────────────────────────

def test_tool_router_user_confirm_succeeds_with_ci_token(tmp_path, temp_workspace):
    """USER_CONFIRM tool succeeds in autonomous pipeline when sealed with a valid CI HMAC token."""
    key = "secret_pipeline_key_123"
    commit = "commit_sha_123"
    repo = "mediaworksrdx-cell/aarkaai3bios"
    nonce_db = tmp_path / "ci_nonces.db"

    token = generate_ci_token(
        signing_key=key,
        repo=repo,
        commit_sha=commit,
        workflow_run_id="ci-run-10",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks"
    )

    approval_ctx = {
        "ci_token": token,
        "ci_signing_key": key,
        "ci_nonce_db": str(nonce_db),
        "commit_sha": commit,
        "repo": repo,
        "force_exec_fallback": True,  # Allow host execution in test environment without Docker
    }

    pipeline = ToolRouterPipeline()
    intents = [
        ToolIntent(
            tool_name="BashTool",
            action="execute",
            params={"command": "echo ci_delegated"},
            confidence=0.99
        )
    ]

    # 1. check_permissions permits intent because valid CI token is provided
    allowed, denied = pipeline.check_permissions(
        user_id="ci_worker",
        intents=intents,
        user_tier="enterprise",
        is_autonomous=True,
        approval_context=approval_ctx,
    )
    assert len(allowed) == 1
    assert len(denied) == 0

    # 2. execute_tools executes through ToolGateway with CI verification
    results = pipeline.execute_tools(
        allowed,
        user_id="ci_worker",
        session_id="ci_session",
        approval_context=approval_ctx,
        workspace_dir=str(temp_workspace),
    )
    assert len(results) == 1
    assert results[0].is_valid is True
    assert results[0].tool_name == "BashTool"


# ─── 5. Subagent Permission Enforcement & Fail-Closed ─────────────────────────

def test_subagent_invoke_tools_permission_enforcement():
    """CognitiveSubagent._invoke_tools() must enforce permissions and block USER_CONFIRM without token."""
    agent = AnalystAgent()
    # Attempt to invoke BashTool which is not in allowed_tools
    results = agent._invoke_tools([
        ("BashTool", "execute", {"command": "ls -la"})
    ])
    # BashTool is skipped since it's not in AnalystAgent.allowed_tools
    assert len(results) == 0

    # Create a custom agent that allows DeployTool
    class DeployerAgent(CognitiveSubagent):
        name = "DeployerAgent"
        allowed_tools = ["DeployTool"]

    deployer = DeployerAgent()
    results = deployer._invoke_tools(
        [("DeployTool", "deploy", {"target": "staging"})],
        context={"user_tier": "enterprise"}
    )

    # Must be blocked by permission gate with an invalid ToolResult
    assert len(results) == 1
    assert results[0].is_valid is False
    assert "Permission Denied" in results[0].error
    assert "Autonomous pipeline blocked USER_CONFIRM" in results[0].error


# ─── 6. Subagent Tool Invocation via ToolGateway ──────────────────────────────

def test_subagent_invoke_tools_routes_through_gateway(temp_workspace):
    """CognitiveSubagent._invoke_tools() dispatches allowed tools through ToolGateway with identity."""
    agent = AnalystAgent()
    # AnalystAgent allows MarketDataTool
    results = agent._invoke_tools(
        [("MarketDataTool", "price", {"symbol": "TCS.NS"})],
        context={
            "user_id": "analyst_user",
            "session_id": "analyst_session",
            "workspace_dir": str(temp_workspace),
        }
    )

    assert len(results) == 1
    assert results[0].tool_name == "MarketDataTool"
    assert results[0].is_valid is True
    assert "TCS.NS" in results[0].data
