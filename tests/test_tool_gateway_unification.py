"""
Unit and Integration Tests for Tool Gateway Unification (v5)

Verifies:
1. BashTool approval enforcement on EXEC path (defense-in-depth).
2. Parameter tampering (args-swap) rejection via action hash recomputation.
3. Atomic CAS single-use consumption and replay rejection (status = 'CONSUMED').
4. Expired approval rejection.
5. Mutating tool approval enforcement.
6. Universal workspace path traversal validation.
7. Classification helpers and fail-closed default for unknown tools.
8. Real on-disk SQLite pre-migration database upgrade without transaction nesting error.
"""
import os
import time
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from modules.approval_store import (
    SQLiteApprovalStore,
    compute_action_hash,
    ToolApprovalRecord,
)
from modules.tool_gateway import (
    ToolGateway,
    ToolGatewayError,
    OperationNotPermittedError,
    ToolClass,
    TOOL_CLASSIFICATIONS,
    is_mutating_tool,
    is_exec_tool,
    is_read_only_tool,
)


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "test_approvals.db"


@pytest.fixture
def temp_workspace(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


@pytest.fixture
def approval_store(temp_db_path):
    return SQLiteApprovalStore(temp_db_path)


@pytest.fixture
def mock_registry():
    registry = MagicMock()
    registry.execute_tool.side_effect = lambda name, args: f"executed_{name}_{args}"
    return registry


# ─── 1. BashTool Gateway Approval Enforcement on EXEC Path ────────────────────

def test_bashtool_claimed_approval_without_approval_id(mock_registry, temp_workspace):
    """Dispatching BashTool with human_approved=True but no approval_id must fail closed."""
    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={"human_approved": True, "force_exec_fallback": True},
        user_id="user1",
        session_id="sess1",
        workspace_dir=str(temp_workspace),
    )
    with pytest.raises(ToolGatewayError, match="claimed human approval without approval_id"):
        gateway.dispatch("BashTool", {"command": "echo test"})


def test_bashtool_claimed_approval_with_fake_approval_id(mock_registry, temp_workspace):
    """Dispatching BashTool with a non-existent approval_id must fail closed."""
    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={
            "human_approved": True,
            "approval_id": "non-existent-id",
            "force_exec_fallback": True,
        },
        user_id="user1",
        session_id="sess1",
        workspace_dir=str(temp_workspace),
    )
    with pytest.raises(ToolGatewayError, match="not found"):
        gateway.dispatch("BashTool", {"command": "echo test"})


# ─── 2. Parameter Tampering (Args-Swap) Detection ─────────────────────────────

def test_bashtool_parameter_tampering_rejected(mock_registry, temp_workspace, approval_store, monkeypatch):
    """Approving 'echo safe' but dispatching 'rm -rf /' must fail closed due to action hash mismatch."""
    monkeypatch.setattr("modules.approval_store.get_approval_store", lambda: approval_store)

    # 1. Create and approve request for safe command
    rec = approval_store.create_request(
        user_id="user1",
        session_id="sess1",
        tool_name="BashTool",
        args={"command": "echo safe"},
        risk_level="HIGH",
        human_summary="Run safe echo",
    )
    approval_store.resolve_request(rec.approval_id, "user1", "APPROVED")

    # 2. Attempt to dispatch with swapped/malicious command
    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={
            "human_approved": True,
            "approval_id": rec.approval_id,
            "force_exec_fallback": True,
        },
        user_id="user1",
        session_id="sess1",
        workspace_dir=str(temp_workspace),
    )
    with pytest.raises(ToolGatewayError, match="Action hash verification failed"):
        gateway.dispatch("BashTool", {"command": "rm -rf /"})


# ─── 3. Single-Use CAS & Replay Rejection ─────────────────────────────────────

def test_bashtool_atomic_consumption_and_replay_prevention(mock_registry, temp_workspace, approval_store, monkeypatch):
    """Dispatching with valid approval succeeds once, transitions record to CONSUMED, and rejects replay."""
    monkeypatch.setattr("modules.approval_store.get_approval_store", lambda: approval_store)

    rec = approval_store.create_request(
        user_id="user1",
        session_id="sess1",
        tool_name="BashTool",
        args={"command": "echo once"},
        risk_level="HIGH",
        human_summary="Run once",
    )
    approval_store.resolve_request(rec.approval_id, "user1", "APPROVED")

    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={
            "human_approved": True,
            "approval_id": rec.approval_id,
            "force_exec_fallback": True,
        },
        user_id="user1",
        session_id="sess1",
        workspace_dir=str(temp_workspace),
    )

    # First execution: must succeed
    result = gateway.dispatch("BashTool", {"command": "echo once"})
    assert "BashTool" in str(result)

    # Verify record in database is now CONSUMED
    stored = approval_store.get_request(rec.approval_id)
    assert stored.status == "CONSUMED"

    # Second execution (replay attempt): must fail closed
    with pytest.raises(ToolGatewayError, match="already been consumed"):
        gateway.dispatch("BashTool", {"command": "echo once"})


# ─── 4. Expiry Enforcement ───────────────────────────────────────────────────

def test_bashtool_expired_approval_rejected(mock_registry, temp_workspace, approval_store, monkeypatch):
    """Expired approval record must be rejected and transitioned to EXPIRED."""
    monkeypatch.setattr("modules.approval_store.get_approval_store", lambda: approval_store)

    rec = approval_store.create_request(
        user_id="user1",
        session_id="sess1",
        tool_name="BashTool",
        args={"command": "echo expired"},
        risk_level="HIGH",
        human_summary="Will expire",
        timeout_seconds=-5.0,  # Pre-expired
    )
    # Manually approve the expired record
    conn = approval_store._get_connection()
    try:
        conn.execute("UPDATE tool_approvals SET status = 'APPROVED' WHERE approval_id = ?;", (rec.approval_id,))
        conn.commit()
    finally:
        conn.close()

    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={
            "human_approved": True,
            "approval_id": rec.approval_id,
            "force_exec_fallback": True,
        },
        user_id="user1",
        session_id="sess1",
        workspace_dir=str(temp_workspace),
    )

    with pytest.raises(ToolGatewayError, match="has expired"):
        gateway.dispatch("BashTool", {"command": "echo expired"})

    stored = approval_store.get_request(rec.approval_id)
    assert stored.status == "EXPIRED"


# ─── 5. Mutating Tool Full Verification ───────────────────────────────────────

def test_mutating_tool_tampering_and_consumption(mock_registry, temp_workspace, approval_store, monkeypatch):
    """FileEditTool must enforce hash verification and atomic single-use consumption."""
    monkeypatch.setattr("modules.approval_store.get_approval_store", lambda: approval_store)

    safe_args = {"path": "safe.txt", "content": "hello"}
    rec = approval_store.create_request(
        user_id="user1",
        session_id="sess1",
        tool_name="FileEditTool",
        args=safe_args,
        risk_level="HIGH",
        human_summary="Edit safe.txt",
    )
    approval_store.resolve_request(rec.approval_id, "user1", "APPROVED")

    # 1. Args tampering (different content)
    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={"human_approved": True, "approval_id": rec.approval_id},
        user_id="user1",
        session_id="sess1",
        workspace_dir=str(temp_workspace),
    )
    with pytest.raises(ToolGatewayError, match="Action hash verification failed"):
        gateway.dispatch("FileEditTool", {"path": "safe.txt", "content": "MALICIOUS"})

    # 2. Legitimate execution consumes approval
    res = gateway.dispatch("FileEditTool", safe_args)
    assert "FileEditTool" in res
    assert approval_store.get_request(rec.approval_id).status == "CONSUMED"

    # 3. Replay fails
    with pytest.raises(ToolGatewayError, match="already been consumed"):
        gateway.dispatch("FileEditTool", safe_args)


# ─── 6. Universal Path Traversal Defense ───────────────────────────────────────

def test_path_traversal_blocked_across_all_tools(mock_registry, temp_workspace):
    """Path traversal escaping workspace must be blocked across read-only, exec, and mutating."""
    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={},
        user_id="user1",
        session_id="sess1",
        workspace_dir=str(temp_workspace),
    )
    with pytest.raises(ToolGatewayError, match="Path traversal detected"):
        gateway.dispatch("FileReadTool", {"path": "../../etc/shadow"})

    with pytest.raises(ToolGatewayError, match="Path traversal detected"):
        gateway.dispatch("FileEditTool", {"path": "../../../system32/cmd.exe", "content": "evil"})


def test_empty_workspace_dir_fails_closed(mock_registry):
    """ToolGateway initialized with empty/whitespace workspace must fail closed."""
    gateway = ToolGateway(
        registry=mock_registry,
        approval_context={},
        user_id="user1",
        session_id="sess1",
        workspace_dir="   ",
    )
    # Clear the default attribute manually to test empty check
    gateway.workspace_dir = ""
    with pytest.raises(ToolGatewayError, match="requires a non-empty workspace_dir"):
        gateway.dispatch("FileReadTool", {"path": "test.txt"})


# ─── 7. Classification Helpers & Fail-Closed Default ──────────────────────────

def test_tool_classifications_and_helpers():
    """Verify all mutating tools classify correctly and unknown tool fails closed."""
    expected_mutating = [
        "FileEditTool", "PatchTool", "FileTool", "FsTool",
        "CreateSkillTool", "UpdateSkillTool", "DeleteSkillTool",
        "DeployTool", "DbMigrateTool", "NotificationTool", "ImageTool"
    ]
    for tool in expected_mutating:
        assert is_mutating_tool(tool), f"{tool} should be classified as mutating"
        assert not is_read_only_tool(tool)

    assert is_exec_tool("BashTool")
    assert is_exec_tool("FinanceCodeTool")

    assert is_read_only_tool("FileReadTool")
    assert is_read_only_tool("SearchTool")

    # Unregistered tool must default to MUTATING (fail-closed)
    assert is_mutating_tool("UnregisteredDangerousTool")
    assert not is_read_only_tool("UnregisteredDangerousTool")


# ─── 8. Real On-Disk SQLite Pre-Migration Fixture DB Test ─────────────────────

def test_real_ondisk_pre_migration_database_upgrade(tmp_path):
    """
    Simulate an existing production database created under v3 schema
    (lacking 'CONSUMED' in CHECK constraint).
    Assert that SQLiteApprovalStore upgrades it cleanly without OperationalError,
    preserves existing records, and allows 'CONSUMED' state transitions.
    """
    db_file = tmp_path / "legacy_v3_approvals.db"

    # 1. Create legacy table with v3 CHECK constraint (no 'CONSUMED')
    conn = sqlite3.connect(str(db_file))
    conn.execute("""
        CREATE TABLE tool_approvals (
            approval_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            args_json TEXT NOT NULL,
            action_hash TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            mcp_server_id TEXT NOT NULL,
            target_resource TEXT NOT NULL,
            risk_level TEXT NOT NULL CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
            human_summary TEXT NOT NULL,
            diff_preview TEXT,
            command_preview TEXT,
            status TEXT NOT NULL CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            resolved_at REAL,
            resolved_by TEXT
        );
    """)
    conn.execute("CREATE INDEX idx_approvals_user ON tool_approvals(user_id, status);")
    conn.execute("CREATE INDEX idx_approvals_expiry ON tool_approvals(expires_at);")

    # Insert pre-existing approval records
    now = time.time()
    conn.execute("""
        INSERT INTO tool_approvals (
            approval_id, user_id, session_id, workspace_id, tool_name,
            args_json, action_hash, policy_version, mcp_server_id,
            target_resource, risk_level, human_summary, status,
            created_at, expires_at
        ) VALUES (
            'legacy-approved-001', 'userA', 'sessA', 'default', 'BashTool',
            '{"command": "uptime"}', 'test_hash_001', '1.0', '',
            '', 'HIGH', 'Check uptime', 'APPROVED', ?, ?
        );
    """, (now, now + 3600))
    conn.commit()
    conn.close()

    # 2. Instantiate SQLiteApprovalStore against this real pre-existing DB
    # Must NOT raise sqlite3.OperationalError: cannot start a transaction within a transaction
    store = SQLiteApprovalStore(db_file)

    # 3. Verify pre-existing records were preserved
    rec = store.get_request("legacy-approved-001")
    assert rec is not None
    assert rec.approval_id == "legacy-approved-001"
    assert rec.status == "APPROVED"
    assert rec.tool_name == "BashTool"

    # 4. Verify updated schema: can atomically consume and set status='CONSUMED'
    # Compute the expected hash for the legacy record
    expected_hash = compute_action_hash(
        tool_name="BashTool",
        args={"command": "uptime"},
        user_id="userA",
        session_id="sessA",
        workspace_id="default",
        policy_version="1.0",
        mcp_server_id="",
        target_resource="",
    )
    # Update record hash to match compute_action_hash
    conn2 = store._get_connection()
    conn2.execute("UPDATE tool_approvals SET action_hash = ? WHERE approval_id = 'legacy-approved-001';", (expected_hash,))
    conn2.commit()
    conn2.close()

    success, msg = store.consume_approval(
        approval_id="legacy-approved-001",
        tool_name="BashTool",
        args={"command": "uptime"},
        user_id="userA",
        session_id="sessA",
    )
    assert success is True, f"Failed to consume approval on migrated DB: {msg}"
    assert store.get_request("legacy-approved-001").status == "CONSUMED"

    # 5. Verify idempotency: instantiating store again causes no error and retains 'CONSUMED'
    store_reopened = SQLiteApprovalStore(db_file)
    rec2 = store_reopened.get_request("legacy-approved-001")
    assert rec2.status == "CONSUMED"


def test_bashtool_unauthorized_execution_fails_closed_even_with_fallback(mock_registry, tmp_path):
    """
    EXEC tools (BashTool) must fail closed if no authorization mechanism
    (human_approved, approval_id, ci_token, or interactive_approval) is provided,
    even when force_exec_fallback=True.
    """
    gateway = ToolGateway(
        registry=mock_registry,
        workspace_dir=str(tmp_path),
        user_id="attacker",
        session_id="session_no_auth",
        approval_context={
            "force_exec_fallback": True,  # Attacker attempts to leverage host fallback
            # No human_approved
            # No approval_id
            # No ci_token
            # No interactive_approval
        },
    )

    with pytest.raises(OperationNotPermittedError, match="requires explicit operator confirmation, approval gate, or CI token"):
        gateway.dispatch("BashTool", {"command": "echo hacked"})

    mock_registry.execute_tool.assert_not_called()

