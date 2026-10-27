"""
Transactional Working Tree Snapshot & Atomic Rollback Recovery Test Suite.
Verifies multi-file point-in-time capture, byte-parity restoration, orphan unlinking,
dynamic file registration, recovery evidence logging, and exception handling.
"""

import hashlib
import os
import pytest
from modules.sparc.snapshot_manager import (
    TransactionalSnapshotManager,
    RollbackError,
    FileSnapshot,
)


@pytest.fixture
def test_files(tmp_path):
    f1 = tmp_path / "existing1.txt"
    f1.write_text("Original content 1", encoding="utf-8")

    f2 = tmp_path / "existing2.bin"
    f2.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

    orphan = tmp_path / "orphan_new.txt"

    return str(f1), str(f2), str(orphan)


def test_snapshot_lifecycle_commit(test_files):
    """Verifies normal commit releases active snapshots."""
    f1, f2, _ = test_files
    mgr = TransactionalSnapshotManager()

    mgr.begin_transaction("tx_commit", [f1, f2])
    assert mgr.is_active("tx_commit")
    assert mgr.active_transaction_count() == 1

    # Modify file
    with open(f1, "w", encoding="utf-8") as f:
        f.write("Mutated content")

    mgr.commit_transaction("tx_commit")
    assert not mgr.is_active("tx_commit")
    assert mgr.active_transaction_count() == 0

    # Mutated content remains persisted
    with open(f1, "r", encoding="utf-8") as f:
        assert f.read() == "Mutated content"


def test_snapshot_lifecycle_rollback_and_byte_parity(test_files):
    """Verifies atomic rollback restores exact original byte parity and unlinks orphans."""
    f1, f2, orphan = test_files
    mgr = TransactionalSnapshotManager()

    orig_f1_bytes = open(f1, "rb").read()
    orig_f2_bytes = open(f2, "rb").read()

    mgr.begin_transaction("tx_rollback", [f1, f2, orphan])

    # 1. Mutate existing files
    with open(f1, "wb") as f:
        f.write(b"Corrupted f1 payload")
    with open(f2, "wb") as f:
        f.write(b"Corrupted f2 payload")

    # 2. Create orphan file
    with open(orphan, "wb") as f:
        f.write(b"New orphan file created during stage")
    assert os.path.exists(orphan)

    # 3. Execute rollback
    evidence = mgr.rollback_transaction("tx_rollback")
    assert evidence["success"] is True
    assert not mgr.is_active("tx_rollback")

    # 4. Verify exact byte parity restored
    assert open(f1, "rb").read() == orig_f1_bytes
    assert open(f2, "rb").read() == orig_f2_bytes

    # 5. Verify orphan file unlinked
    assert not os.path.exists(orphan)


def test_snapshot_dynamic_registration(test_files):
    """Verifies registering a newly created file dynamically during a transaction."""
    f1, _, orphan = test_files
    mgr = TransactionalSnapshotManager()

    mgr.begin_transaction("tx_dyn", [f1])

    # Dynamic registration of anticipated orphan file
    mgr.register_file("tx_dyn", orphan)
    with open(orphan, "w", encoding="utf-8") as f:
        f.write("Dynamically created")
    assert os.path.exists(orphan)

    # Rollback should clean up the dynamically registered orphan
    mgr.rollback_transaction("tx_dyn")
    assert not os.path.exists(orphan)


def test_repeated_rollback_rejected(test_files):
    """Verifies attempting to rollback an already rolled-back transaction raises KeyError."""
    f1, _, _ = test_files
    mgr = TransactionalSnapshotManager()
    mgr.begin_transaction("tx_repeat", [f1])
    mgr.rollback_transaction("tx_repeat")

    with pytest.raises(KeyError, match="No active transaction found"):
        mgr.rollback_transaction("tx_repeat")


def test_duplicate_begin_transaction_rejected(test_files):
    """Verifies that opening an existing transaction ID raises ValueError."""
    f1, _, _ = test_files
    mgr = TransactionalSnapshotManager()
    mgr.begin_transaction("tx_dup", [f1])

    with pytest.raises(ValueError, match="already active"):
        mgr.begin_transaction("tx_dup", [f1])
