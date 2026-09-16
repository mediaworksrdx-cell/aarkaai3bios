"""
Unit tests for fail-closed, hash-chained security audit logger.
"""
import time
import json
import pytest
from pathlib import Path
from modules.security_audit import SecurityAuditLogger, SecurityAuditError


@pytest.fixture
def audit_logger(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    spool_file = tmp_path / "spool.jsonl"
    return SecurityAuditLogger(log_path=log_file, spool_path=spool_file, fail_closed=True)


def test_audit_event_hash_chaining(audit_logger):
    h1 = audit_logger.log_event("test.event_1", {"msg": "first"})
    assert len(h1) == 64

    h2 = audit_logger.log_event("test.event_2", {"msg": "second"})
    assert len(h2) == 64
    assert h1 != h2

    # Verify chain in log file
    with open(audit_logger.log_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    assert len(lines) == 2
    assert lines[0]["record_hash"] == h1
    assert lines[0]["prev_record_hash"] == "0" * 64
    assert lines[1]["record_hash"] == h2
    assert lines[1]["prev_record_hash"] == h1


def test_sensitive_field_minimization(audit_logger):
    audit_logger.log_event("test.secret", {
        "api_key": "sk-1234567890abcdef1234567890",
        "normal_field": "visible_value"
    })
    with open(audit_logger.log_path, "r", encoding="utf-8") as f:
        rec = json.loads(f.readline())

    details = rec["details"]
    assert details["normal_field"] == "visible_value"
    assert "sk-1234567890abcdef1234567890" not in str(details)
    assert "sha256" in details["api_key"]


def test_fail_closed_on_write_failure(tmp_path):
    read_only_dir = tmp_path / "readonly_dir"
    read_only_dir.mkdir()
    log_file = read_only_dir / "audit.jsonl"
    spool_file = read_only_dir / "spool.jsonl"

    sal = SecurityAuditLogger(log_path=log_file, spool_path=spool_file, fail_closed=True)

    # Make target read-only / unwriteable to trigger I/O error
    try:
        import stat
        log_file.chmod(stat.S_IREAD)
        with pytest.raises(SecurityAuditError):
            sal.log_event("test.fail_closed", {"foo": "bar"})
    finally:
        log_file.chmod(stat.S_IWRITE | stat.S_IREAD)


def test_spool_age_check_privileged_fail_closed(audit_logger):
    # Simulate an entry older than 300s in spool
    old_time = time.time() - 350.0
    spool_entry = {
        "timestamp": old_time,
        "record_hash": "a" * 64,
        "event_type": "old.event"
    }
    with open(audit_logger.spool_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(spool_entry) + "\n")

    with pytest.raises(SecurityAuditError, match="Audit spool unanchored age"):
        audit_logger.check_spool_health_for_privileged_operation()


def test_spool_acknowledged_removes_entries(audit_logger):
    h1 = audit_logger.log_event("e1", {})
    h2 = audit_logger.log_event("e2", {})
    assert audit_logger.spool_path.exists()

    # Acknowledge up to h1
    audit_logger.acknowledge_spool_anchored(h1)

    with open(audit_logger.spool_path, "r", encoding="utf-8") as f:
        remaining = [json.loads(line) for line in f if line.strip()]

    assert len(remaining) == 1
    assert remaining[0]["record_hash"] == h2
