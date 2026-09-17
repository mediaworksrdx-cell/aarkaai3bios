"""
Unit tests for Hardened Code Mode Sandbox Engine.
Validates zero host fallback, mutating tool approval gates (human & CI token),
workspace quotas, timeout cleanup, AST evasion resistance, and safe ReAct fallback restrictions.
"""
import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from modules.code_mode import (
    CodeModeExecutor,
    CodeModeResult,
    SandboxUnavailableError,
    OperationNotPermittedError,
    StorageQuotaExceededError,
    MUTATING_TOOLS,
    SAFE_FALLBACK_TOOLS
)
from modules.ci_nonce_store import generate_ci_token, CINonceStore


@pytest.fixture
def mock_registry():
    reg = MagicMock()
    reg.tools = {
        "FileReadTool": MagicMock(description="Reads file"),
        "SearchTool": MagicMock(description="Searches code"),
        "BashTool": MagicMock(description="Executes bash"),
        "FileEditTool": MagicMock(description="Edits file"),
        "DeployTool": MagicMock(description="Deploys app")
    }
    reg.execute_tool.return_value = "Tool execution output"
    return reg


def test_docker_missing_aborts_without_host_fallback(mock_registry, tmp_path):
    """Enforce zero host fallback: if Docker is unavailable, raise SandboxUnavailableError."""
    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        force_mock_container=False
    )

    with patch.object(CodeModeExecutor, "is_docker_available", return_value=False):
        namespace = executor.build_tool_namespace(["FileReadTool"])
        with pytest.raises(SandboxUnavailableError, match="Docker container daemon is not accessible"):
            executor.execute_code_block("x = 10", namespace, user_id="user1", session_id="sess1")


def test_script_size_exceeded_rejected(mock_registry, tmp_path):
    """Scripts exceeding max_script_bytes (64 KB) are rejected immediately."""
    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        max_script_bytes=1000,
        force_mock_container=True
    )
    namespace = executor.build_tool_namespace(["FileReadTool"])
    huge_script = "# comment\n" * 200  # > 1000 bytes
    res = executor.execute_code_block(huge_script, namespace, user_id="u", session_id="s")
    assert not res.success
    assert "exceeds cap" in res.error


def test_workspace_file_count_cap_enforced(mock_registry, tmp_path):
    """Workspace exceeding max_workspace_files triggers StorageQuotaExceededError."""
    test_dir = tmp_path / "workspace_test"
    test_dir.mkdir()
    for i in range(6):
        (test_dir / f"file_{i}.txt").write_text("data")

    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(test_dir),
        max_workspace_files=5,
        force_mock_container=True
    )

    with pytest.raises(StorageQuotaExceededError, match="Workspace file count"):
        executor._check_workspace_quotas(test_dir)


def test_workspace_quota_low_space_rejected(mock_registry, tmp_path):
    """Workspace with available bytes below threshold triggers StorageQuotaExceededError."""
    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        max_workspace_bytes=100 * 1024 * 1024,
        force_mock_container=True
    )

    # Mock disk_usage / statvfs to return 1 MB available (threshold is max(5MB, 5%) = 5MB)
    with patch("shutil.disk_usage") as mock_usage:
        mock_usage.return_value = MagicMock(free=1024 * 1024)
        if hasattr(os, "statvfs"):
            with patch("os.statvfs") as mock_vfs:
                vfs_obj = MagicMock()
                vfs_obj.f_bavail = 100
                vfs_obj.f_frsize = 1024  # 100 KB
                vfs_obj.f_favail = 1000
                mock_vfs.return_value = vfs_obj
                with pytest.raises(StorageQuotaExceededError, match="disk space critically low"):
                    executor._check_workspace_quotas(tmp_path)
        else:
            with pytest.raises(StorageQuotaExceededError, match="disk space critically low"):
                executor._check_workspace_quotas(tmp_path)


def test_mutating_tool_requires_approval(mock_registry, tmp_path):
    """Mutating tools raise OperationNotPermittedError when approval is not provided."""
    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        approval_context={}
    )
    namespace = executor.build_tool_namespace(["BashTool", "DeployTool", "FileReadTool"])

    # Read-only tool succeeds
    assert namespace["FileReadTool"](path="test.py") == "Tool execution output"

    # Mutating tools fail closed
    for tool_name in ["BashTool", "DeployTool"]:
        with pytest.raises(OperationNotPermittedError, match="requires explicit operator confirmation"):
            namespace[tool_name](command="ls")


def test_mutating_tool_approved_with_human_flag(mock_registry, tmp_path):
    """Mutating tools succeed when human_approved=True is in approval_context."""
    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        approval_context={"human_approved": True}
    )
    namespace = executor.build_tool_namespace(["BashTool", "FileEditTool"])

    res1 = namespace["BashTool"](command="echo safe")
    assert res1 == "Tool execution output"
    res2 = namespace["FileEditTool"](path="foo.txt", content="bar")
    assert res2 == "Tool execution output"


def test_mutating_tool_approved_with_ci_token(mock_registry, tmp_path):
    """Mutating tools succeed when verified with a cryptographically sealed CI token."""
    key = "ci_secret_test_key_123"
    commit = "commit_valid_abc"
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

    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        approval_context={
            "ci_token": token,
            "ci_signing_key": key,
            "ci_nonce_db": str(nonce_db),
            "commit_sha": commit,
            "repo": repo
        }
    )
    namespace = executor.build_tool_namespace(["BashTool"])

    # First call succeeds
    res = namespace["BashTool"](command="make test")
    assert res == "Tool execution output"

    # Second call with the same token fails (nonce replayed)
    with pytest.raises(OperationNotPermittedError, match="Token replay detected"):
        namespace["BashTool"](command="make test")


def test_mock_subprocess_execution_success(mock_registry, tmp_path):
    """Verify end-to-end execution of Python code block with IPC tool call."""
    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        force_mock_container=True
    )
    namespace = executor.build_tool_namespace(["FileReadTool"])

    code = "res = FileReadTool(path='test.py')\nprint(f'Done: {res}')"
    res = executor.execute_code_block(code, namespace, user_id="u1", session_id="s1")

    assert res.success is True
    assert "Done: Tool execution output" in res.output
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0]["tool"] == "FileReadTool"


def test_mock_subprocess_execution_timeout(mock_registry, tmp_path):
    """Long-running script is terminated by the watchdog timer."""
    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        timeout=0.3,
        force_mock_container=True
    )
    namespace = executor.build_tool_namespace(["FileReadTool"])

    # Busy loop without forbidden imports
    code = "count = 0\nfor i in range(100_000_000):\n    count += 1"
    res = executor.execute_code_block(code, namespace, user_id="u1", session_id="s1")

    assert res.success is False
    assert "timed out" in res.error.lower()


def test_ast_validation_evasion_blocked():
    """Verify AST validator rejects evasion patterns."""
    evasions = [
        ("x = ().__class__", "Forbidden attribute: __class__"),
        ("x = ().__subclasses__()", "Forbidden attribute: __subclasses__"),
        ("x = [].__builtins__", "Forbidden attribute: __builtins__"),
        ("f = open('foo.txt')", "Forbidden builtin: open"),
        ("v = eval('1 + 1')", "Forbidden builtin: eval"),
        ("v = exec('x = 1')", "Forbidden builtin: exec"),
        ("import os", "Forbidden import: os"),
        ("import subprocess", "Forbidden import: subprocess"),
        ("from socket import socket", "Forbidden import: socket"),
    ]
    for code, expected_err in evasions:
        valid, err = CodeModeExecutor.validate_code(code)
        assert not valid, f"Code '{code}' should have been rejected"
        assert expected_err in err


def test_safe_fallback_tools_containment():
    """Verify SAFE_FALLBACK_TOOLS contains only read-only safe tools and zero mutating tools."""
    assert "FileReadTool" in SAFE_FALLBACK_TOOLS
    assert "SearchTool" in SAFE_FALLBACK_TOOLS

    for mutating in MUTATING_TOOLS:
        assert mutating not in SAFE_FALLBACK_TOOLS


def test_interactive_approval_gate_flow(mock_registry, tmp_path):
    """Test interactive approval gate with ApprovalStore: approved vs rejected."""
    import threading
    from modules.approval_store import get_approval_store

    store = get_approval_store()
    emitted_events = []

    def mock_emitter(event):
        emitted_events.append(event)
        # Automatically approve in background thread
        appr_id = event["payload"]["approval_id"]
        t = threading.Thread(target=lambda: store.resolve_request(appr_id, "test_user", "APPROVED"))
        t.start()

    executor = CodeModeExecutor(
        tool_registry=mock_registry,
        workspace_dir=str(tmp_path),
        approval_context={
            "interactive_approval": True,
            "user_id": "test_user",
            "session_id": "test_sess",
            "approval_timeout": 5.0,
            "event_emitter": mock_emitter
        }
    )

    namespace = executor.build_tool_namespace(["BashTool"])
    res = namespace["BashTool"](cmd="ls -la")
    assert res == "Tool execution output"
    assert len(emitted_events) == 1
    assert emitted_events[0]["type"] == "approval_request"
    assert emitted_events[0]["payload"]["tool_name"] == "BashTool"


def test_coordinator_rejection_stops_execution_without_proceeding(monkeypatch):
    """Verify coordinator terminates immediately upon rejection and does not pretend work was done."""
    import threading
    from modules import coordinator, aarkaa_engine
    from modules.approval_store import get_approval_store

    store = get_approval_store()

    # Mock aarkaa_engine.generate_raw to emit a FileEditTool call
    step = 0
    def mock_generate_raw(*args, **kwargs):
        nonlocal step
        step += 1
        return 'Thought: I need to edit the file.\nAction: FileEditTool\nAction Input: {"path": "test_script.py", "content": "print(1)"}'

    monkeypatch.setattr(aarkaa_engine, "generate_raw", mock_generate_raw)

    events = []
    def auto_reject_worker():
        import time
        for _ in range(500):
            time.sleep(0.02)
            for ev_type, ev_data in list(events):
                if ev_type == "approval_request":
                    appr_id = ev_data["approval_id"]
                    store.resolve_request(appr_id, "u_test", "REJECTED")
                    return

    t = threading.Thread(target=auto_reject_worker)
    t.start()

    for ev_type, ev_data in coordinator.stream_task("Write a script", user_id="u_test", session_id="s_test"):
        events.append((ev_type, ev_data))

    t.join()

    event_types = [e[0] for e in events]
    assert "approval_request" in event_types
    assert "approval_resolved" in event_types

    # Find final answer
    final_events = [e[1] for e in events if e[0] == "final"]
    assert len(final_events) == 1
    final_text = final_events[0]
    assert "Operation cancelled" in final_text
    assert "was not approved" in final_text
    assert "I already wrote this file" not in final_text
    assert "I will now run it using BashTool" not in final_text


