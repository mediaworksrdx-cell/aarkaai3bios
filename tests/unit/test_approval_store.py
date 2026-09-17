"""
Tests for modules.approval_store:
Verifies atomic CAS state machine, multi-worker coordination, deep action hash tampering,
replay protection, expiration races, and tenant isolation.
"""
import time
import pytest
import threading
from pathlib import Path
from modules.approval_store import (
    SQLiteApprovalStore,
    compute_action_hash,
    ToolApprovalRecord,
    ApprovalResponse
)


@pytest.fixture
def temp_store(tmp_path):
    db_file = tmp_path / "test_approvals.db"
    store = SQLiteApprovalStore(db_path=db_file)
    return store


def test_create_and_get_request(temp_store):
    rec = temp_store.create_request(
        user_id="user_123",
        session_id="sess_abc",
        tool_name="FileEditTool",
        args={"path": "src/main.py", "content": "print('hello')"},
        risk_level="HIGH",
        human_summary="Modify file src/main.py",
        workspace_id="ws_default",
        diff_preview="+ print('hello')",
        timeout_seconds=60.0
    )

    assert rec.approval_id.startswith("appr_")
    assert rec.status == "PENDING"
    assert rec.user_id == "user_123"
    assert len(rec.action_hash) == 64

    fetched = temp_store.get_request(rec.approval_id)
    assert fetched is not None
    assert fetched.approval_id == rec.approval_id
    assert fetched.action_hash == rec.action_hash
    assert fetched.tool_name == "FileEditTool"
    assert fetched.status == "PENDING"


def test_atomic_approval_resolution(temp_store):
    rec = temp_store.create_request(
        user_id="user_1",
        session_id="s1",
        tool_name="BashTool",
        args={"cmd": "git status"},
        risk_level="MEDIUM",
        human_summary="Run git status"
    )

    resp = temp_store.resolve_request(rec.approval_id, "user_1", "APPROVED")
    assert resp.status == "approved"
    assert resp.approval_id == rec.approval_id

    # Verify state in DB
    updated = temp_store.get_request(rec.approval_id)
    assert updated.status == "APPROVED"
    assert updated.resolved_by == "user_1"
    assert updated.resolved_at is not None


def test_atomic_rejection_resolution(temp_store):
    rec = temp_store.create_request(
        user_id="user_1",
        session_id="s1",
        tool_name="DeployTool",
        args={"target": "prod"},
        risk_level="CRITICAL",
        human_summary="Deploy to production"
    )

    resp = temp_store.resolve_request(rec.approval_id, "user_1", "REJECTED")
    assert resp.status == "rejected"

    updated = temp_store.get_request(rec.approval_id)
    assert updated.status == "REJECTED"


def test_replay_protection(temp_store):
    rec = temp_store.create_request(
        user_id="user_1",
        session_id="s1",
        tool_name="BashTool",
        args={"cmd": "ls -la"},
        risk_level="LOW",
        human_summary="List files"
    )

    resp1 = temp_store.resolve_request(rec.approval_id, "user_1", "APPROVED")
    assert resp1.status == "approved"

    # Second resolution attempt must be rejected as already resolved
    resp2 = temp_store.resolve_request(rec.approval_id, "user_1", "APPROVED")
    assert resp2.status == "approved"
    assert "already in state" in resp2.message.lower()

    # Rejection attempt on approved record must also fail
    resp3 = temp_store.resolve_request(rec.approval_id, "user_1", "REJECTED")
    assert resp3.status == "approved"
    assert "already in state" in resp3.message.lower()


def test_tenant_isolation(temp_store):
    rec = temp_store.create_request(
        user_id="alice",
        session_id="s_alice",
        tool_name="FileEditTool",
        args={"path": "alice_secrets.txt"},
        risk_level="HIGH",
        human_summary="Edit Alice file"
    )

    # Bob attempts to approve Alice's request
    resp = temp_store.resolve_request(rec.approval_id, "bob", "APPROVED")
    assert resp.status == "unauthorized"
    assert "does not own" in resp.message.lower()

    # Record must still be PENDING
    assert temp_store.get_request(rec.approval_id).status == "PENDING"


def test_expiry_enforcement(temp_store):
    rec = temp_store.create_request(
        user_id="user_1",
        session_id="s1",
        tool_name="BashTool",
        args={"cmd": "rm -rf /tmp/scratch"},
        risk_level="HIGH",
        human_summary="Delete scratch",
        timeout_seconds=0.1  # 100ms
    )

    time.sleep(0.15)  # Wait for expiration

    # Resolving expired request must transition to EXPIRED and fail
    resp = temp_store.resolve_request(rec.approval_id, "user_1", "APPROVED")
    assert resp.status == "expired"

    updated = temp_store.get_request(rec.approval_id)
    assert updated.status == "EXPIRED"


def test_expiry_race_condition(temp_store):
    """
    Simulates race between background expiry and user clicking approve simultaneously.
    Verifies exactly ONE transition wins atomically.
    """
    rec = temp_store.create_request(
        user_id="user_1",
        session_id="s1",
        tool_name="FileEditTool",
        args={"path": "app.py"},
        risk_level="MEDIUM",
        human_summary="Edit app.py",
        timeout_seconds=0.2
    )

    results = []

    def try_approve():
        r = temp_store.resolve_request(rec.approval_id, "user_1", "APPROVED")
        results.append(("approve", r.status))

    def try_expire():
        time.sleep(0.2)
        temp_store.cancel_and_expire_stale(now=time.time() + 0.1)
        r = temp_store.get_request(rec.approval_id)
        results.append(("expire", r.status if r else "none"))

    t1 = threading.Thread(target=try_approve)
    t2 = threading.Thread(target=try_expire)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    final_rec = temp_store.get_request(rec.approval_id)
    # The final record status must be either strictly APPROVED or EXPIRED, never inconsistent
    assert final_rec.status in ("APPROVED", "EXPIRED")


def test_action_hash_tampering_detection(temp_store):
    rec = temp_store.create_request(
        user_id="user_1",
        session_id="s1",
        tool_name="FileEditTool",
        args={"path": "safe.py", "code": "x = 1"},
        risk_level="HIGH",
        human_summary="Edit safe.py"
    )

    original_hash = rec.action_hash

    # Approve request normally
    temp_store.resolve_request(rec.approval_id, "user_1", "APPROVED")

    # Await resolution with an altered expected hash (simulating modified arguments)
    tampered_hash = compute_action_hash(
        tool_name="FileEditTool",
        args={"path": "safe.py", "code": "x = 999; os.system('malicious')"},  # Tampered!
        user_id="user_1",
        session_id="s1"
    )

    success, msg = temp_store.await_resolution(rec.approval_id, expected_action_hash=tampered_hash, timeout_seconds=1.0)
    assert not success
    assert "verification failed" in msg.lower() or "altered" in msg.lower()

    # When providing exact original hash, verification succeeds
    success2, msg2 = temp_store.await_resolution(rec.approval_id, expected_action_hash=original_hash, timeout_seconds=1.0)
    assert success2
    assert "approved" in msg2.lower()


def test_multi_worker_concurrency_simulation(temp_store):
    """
    Simulates Worker A creating a request and awaiting, while Worker B resolves it.
    """
    rec = temp_store.create_request(
        user_id="worker_user",
        session_id="worker_sess",
        tool_name="BashTool",
        args={"cmd": "pytest"},
        risk_level="LOW",
        human_summary="Run pytest",
        timeout_seconds=5.0
    )

    worker_a_result = []

    def worker_a_await():
        success, msg = temp_store.await_resolution(rec.approval_id, rec.action_hash, timeout_seconds=4.0)
        worker_a_result.append((success, msg))

    def worker_b_resolve():
        time.sleep(0.2)
        resp = temp_store.resolve_request(rec.approval_id, "worker_user", "APPROVED")
        assert resp.status == "approved"

    t_a = threading.Thread(target=worker_a_await)
    t_b = threading.Thread(target=worker_b_resolve)

    t_a.start()
    t_b.start()
    t_a.join()
    t_b.join()

    assert len(worker_a_result) == 1
    assert worker_a_result[0][0] is True
    assert "approved" in worker_a_result[0][1].lower()


def test_audit_hash_chain_integrity(tmp_path):
    from modules.security_audit import SecurityAuditLogger, verify_audit_log_integrity

    test_log = tmp_path / "test_audit.jsonl"
    test_spool = tmp_path / "test_spool.jsonl"
    logger_instance = SecurityAuditLogger(log_path=test_log, spool_path=test_spool)

    # Log 3 events
    h1 = logger_instance.log_event("event.one", {"detail": "alpha"})
    h2 = logger_instance.log_event("event.two", {"detail": "beta"})
    h3 = logger_instance.log_event("event.three", {"detail": "gamma"})

    valid, count, err = verify_audit_log_integrity(test_log)
    assert valid is True
    assert count == 3
    assert err is None

    # Simulate tampering with the file: modify event.two payload
    content = test_log.read_text(encoding="utf-8")
    tampered_content = content.replace('"beta"', '"tampered_value"')
    test_log.write_text(tampered_content, encoding="utf-8")

    # Verification must fail and detect tampering
    valid2, count2, err2 = verify_audit_log_integrity(test_log)
    assert valid2 is False
    assert "tampering detected" in err2.lower()

