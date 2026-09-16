"""
Unit tests for Durable SQLite WAL Nonce Store and CI Token Verification.
Covers constant-time HMAC, clock skew tolerance, key ID rotation, replay rejection,
concurrent write serialization, scope escalation rejection, and storage GC cleanup.
"""
import time
import sqlite3
import pytest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from modules.ci_nonce_store import (
    CINonceStore,
    generate_ci_token,
    verify_ci_approval_token,
    DEFAULT_AUTH_WINDOW_SECONDS,
    CLOCK_SKEW_TOLERANCE_SECONDS
)


@pytest.fixture
def nonce_store(tmp_path):
    db_file = tmp_path / "test_ci_nonces.db"
    return CINonceStore(db_path=db_file)


def test_ci_token_valid_constant_time_hmac(nonce_store):
    key = "super_secret_signing_key_32_bytes_min"
    token = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="a1b2c3d4e5f67890",
        workflow_run_id="run-101",
        job_id="job-202",
        tool_scope="non-destructive-benchmarks",
        kid="k1"
    )

    valid, reason = verify_ci_approval_token(
        token=token,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="a1b2c3d4e5f67890",
        nonce_store=nonce_store
    )
    assert valid is True
    assert reason == "Token verified and consumed"


def test_ci_token_replay_nonce_rejected_across_instances(nonce_store, tmp_path):
    key = "test_key_replay"
    token = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit123",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks"
    )

    # First consumption succeeds
    valid1, _ = verify_ci_approval_token(
        token=token,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit123",
        nonce_store=nonce_store
    )
    assert valid1 is True

    # Second consumption of the same token using a separate store instance pointing to same DB fails
    store2 = CINonceStore(db_path=nonce_store.db_path)
    valid2, reason2 = verify_ci_approval_token(
        token=token,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit123",
        nonce_store=store2
    )
    assert valid2 is False
    assert "replay detected" in reason2.lower()


def test_ci_token_clock_skew_tolerance(nonce_store):
    key = "test_key_skew"
    now = time.time()

    # Token issued 20s in the future (within 30s skew tolerance)
    token_future = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_skew",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks",
        now=now + 20.0
    )

    valid, reason = verify_ci_approval_token(
        token=token_future,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_skew",
        nonce_store=nonce_store,
        now=now
    )
    assert valid is True

    # Token issued 45s in the future (exceeds 30s skew tolerance)
    token_too_early = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_skew",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks",
        now=now + 45.0
    )

    valid_early, reason_early = verify_ci_approval_token(
        token=token_too_early,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_skew",
        nonce_store=nonce_store,
        now=now
    )
    assert valid_early is False
    assert "not yet valid" in reason_early


def test_ci_token_expired_rejected(nonce_store):
    key = "test_key_expired"
    now = time.time()

    # Token issued 350s ago with 300s window (expired even with 30s tolerance)
    token_expired = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_exp",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks",
        expires_in_seconds=300.0,
        now=now - 350.0
    )

    valid, reason = verify_ci_approval_token(
        token=token_expired,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_exp",
        nonce_store=nonce_store,
        now=now
    )
    assert valid is False
    assert "expired" in reason.lower()


def test_ci_token_key_id_validation_and_rotation(nonce_store):
    old_key = "old_secret_key_v1"
    new_key = "new_secret_key_v2"
    key_ring = {"k1": old_key, "k2": new_key}

    # Token signed with k2
    token_k2 = generate_ci_token(
        signing_key=new_key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_rot",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks",
        kid="k2"
    )

    valid, _ = verify_ci_approval_token(
        token=token_k2,
        signing_keys=key_ring,
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_rot",
        nonce_store=nonce_store
    )
    assert valid is True

    # Token with untrusted kid
    token_unknown = generate_ci_token(
        signing_key="other_key",
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_rot",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks",
        kid="k999"
    )

    valid_unk, reason_unk = verify_ci_approval_token(
        token=token_unknown,
        signing_keys=key_ring,
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_rot",
        nonce_store=nonce_store
    )
    assert valid_unk is False
    assert "Unknown or untrusted key ID" in reason_unk


def test_ci_token_commit_sha_mismatch_rejected(nonce_store):
    key = "test_key_mismatch"
    token = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_correct",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks"
    )

    valid, reason = verify_ci_approval_token(
        token=token,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_tampered",
        nonce_store=nonce_store
    )
    assert valid is False
    assert "Commit SHA mismatch" in reason


def test_ci_token_scope_escalation_rejected(nonce_store):
    key = "test_key_scope"

    # 1. Unapproved scope
    token_unapproved = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_1",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="unrestricted-admin-access"
    )
    valid, reason = verify_ci_approval_token(
        token=token_unapproved,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_1",
        nonce_store=nonce_store
    )
    assert valid is False
    assert "not permitted for CI automated approval" in reason

    # 2. Forbidden destructive operation
    token_forbidden = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_2",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="file_delete"
    )
    valid2, reason2 = verify_ci_approval_token(
        token=token_forbidden,
        signing_keys={"k1": key},
        expected_repo="mediaworksrdx-cell/aarkaai3bios",
        expected_commit="commit_2",
        nonce_store=nonce_store
    )
    assert valid2 is False


def test_ci_token_concurrent_processes_no_race(nonce_store):
    key = "test_key_concurrent"
    token = generate_ci_token(
        signing_key=key,
        repo="mediaworksrdx-cell/aarkaai3bios",
        commit_sha="commit_conc",
        workflow_run_id="run-1",
        job_id="job-1",
        tool_scope="non-destructive-benchmarks"
    )

    results = []

    def attempt_verify():
        store = CINonceStore(db_path=nonce_store.db_path)
        valid, _ = verify_ci_approval_token(
            token=token,
            signing_keys={"k1": key},
            expected_repo="mediaworksrdx-cell/aarkaai3bios",
            expected_commit="commit_conc",
            nonce_store=store
        )
        return valid

    # Run 10 threads trying to consume the same token simultaneously
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_verify) for _ in range(10)]
        results = [f.result() for f in futures]

    # Exactly one thread must succeed, 9 must fail
    assert results.count(True) == 1
    assert results.count(False) == 9


def test_nonce_cleanup_expired_retention(nonce_store):
    now = time.time()
    # Insert old nonces (>600s ago) and recent nonces (<600s ago)
    with nonce_store._get_connection() as conn:
        conn.execute(
            "INSERT INTO consumed_nonces (nonce, commit_sha, consumed_at) VALUES (?, ?, ?);",
            ("old_nonce_1", "sha1", now - 700.0)
        )
        conn.execute(
            "INSERT INTO consumed_nonces (nonce, commit_sha, consumed_at) VALUES (?, ?, ?);",
            ("old_nonce_2", "sha2", now - 650.0)
        )
        conn.execute(
            "INSERT INTO consumed_nonces (nonce, commit_sha, consumed_at) VALUES (?, ?, ?);",
            ("recent_nonce", "sha3", now - 100.0)
        )

    deleted = nonce_store.cleanup_expired_nonces(now=now, retention_seconds=600.0)
    assert deleted == 2

    # Verify only recent_nonce remains
    with nonce_store._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nonce FROM consumed_nonces;")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "recent_nonce"
