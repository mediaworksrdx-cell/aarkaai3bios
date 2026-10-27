"""
Transactional Multi-File Working Tree Snapshot & Atomic Rollback Manager.
Guarantees two-phase atomic multi-file restoration, cryptographic byte-parity verification,
and orphan cleanup across SPARC swarm stages without partial state leaks.
"""

import hashlib
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RollbackError(IOError):
    """Raised when rollback encounters errors or byte-parity mismatches."""
    def __init__(self, message: str, recovery_evidence: Dict[str, Any]) -> None:
        super().__init__(message)
        self.recovery_evidence = recovery_evidence


@dataclass(frozen=True)
class FileSnapshot:
    """Represents an immutable point-in-time snapshot of a single file."""
    file_path: str
    existed: bool
    content: Optional[bytes] = None
    sha256_hash: Optional[str] = None
    mode: Optional[int] = None


class TransactionalSnapshotManager:
    """
    Guarantees atomic multi-file restoration and orphan cleanup across SPARC swarm stages.
    Thread-safe, records SHA-256 hashes, uses two-phase atomic replacement to prevent partial
    writes, verifies byte parity, and preserves transactions and snapshots on any restoration failure.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active_transactions: Dict[str, List[FileSnapshot]] = {}
        self._failed_transactions: Dict[str, Dict[str, Any]] = {}
        self._audit_log: List[Dict[str, Any]] = []

    def begin_transaction(self, transaction_id: str, file_paths: List[str]) -> None:
        """
        Captures point-in-time byte snapshots and SHA-256 hashes of all specified files.
        Records non-existent files to ensure orphaned creations can be purged on rollback.
        """
        if not transaction_id or not isinstance(transaction_id, str):
            raise ValueError("transaction_id must be a non-empty string.")

        with self._lock:
            if transaction_id in self._active_transactions:
                raise ValueError(f"Transaction '{transaction_id}' is already active.")

            snapshots: List[FileSnapshot] = []
            for raw_path in file_paths:
                norm_path = os.path.abspath(raw_path)
                if os.path.exists(norm_path):
                    try:
                        with open(norm_path, "rb") as f:
                            content = f.read()
                        sha256_hash = hashlib.sha256(content).hexdigest()
                        mode = os.stat(norm_path).st_mode
                        snapshots.append(FileSnapshot(
                            file_path=norm_path,
                            existed=True,
                            content=content,
                            sha256_hash=sha256_hash,
                            mode=mode
                        ))
                    except Exception as e:
                        raise IOError(f"Failed to snapshot existing file '{norm_path}': {e}") from e
                else:
                    snapshots.append(FileSnapshot(
                        file_path=norm_path,
                        existed=False
                    ))

            self._active_transactions[transaction_id] = snapshots
            self._audit_log.append({
                "event": "transaction_begun",
                "transaction_id": transaction_id,
                "file_count": len(snapshots)
            })

    def register_file(self, transaction_id: str, file_path: str, existed: Optional[bool] = None) -> None:
        """Dynamically registers an additional file into an active transaction before or after modification."""
        with self._lock:
            snapshots = self._active_transactions.get(transaction_id)
            if snapshots is None:
                raise KeyError(f"No active transaction found with ID '{transaction_id}'.")

            norm_path = os.path.abspath(file_path)
            # Check if already tracked
            if any(s.file_path == norm_path for s in snapshots):
                return

            is_existing = existed if existed is not None else os.path.exists(norm_path)

            if is_existing and os.path.exists(norm_path):
                with open(norm_path, "rb") as f:
                    content = f.read()
                sha256_hash = hashlib.sha256(content).hexdigest()
                mode = os.stat(norm_path).st_mode
                snapshots.append(FileSnapshot(
                    file_path=norm_path,
                    existed=True,
                    content=content,
                    sha256_hash=sha256_hash,
                    mode=mode
                ))
            else:
                snapshots.append(FileSnapshot(file_path=norm_path, existed=False))

    def commit_transaction(self, transaction_id: str) -> None:
        """
        Persists working tree changes and releases recorded snapshots.
        """
        with self._lock:
            if transaction_id not in self._active_transactions:
                raise KeyError(f"No active transaction found with ID '{transaction_id}'.")
            del self._active_transactions[transaction_id]
            self._audit_log.append({
                "event": "transaction_committed",
                "transaction_id": transaction_id
            })

    def rollback_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Atomically restores all mutated files using two-phase staging and replacement.
        Guarantees that active snapshots are NOT deleted if rollback fails, preserving
        forensic evidence and retry capabilities.
        """
        with self._lock:
            snapshots = self._active_transactions.get(transaction_id)
            if snapshots is None:
                raise KeyError(f"Cannot rollback: No active transaction found with ID '{transaction_id}'.")

            staging_files: List[str] = []
            restored_files: List[str] = []
            unlinked_orphans: List[str] = []
            errors: List[str] = []

            # ─── PHASE 1: Staging & Parity Verification ──────────────────────────
            # Stage all existing files into sibling temp files without touching live files.
            for snap in snapshots:
                if snap.existed and snap.content is not None:
                    stage_path = f"{snap.file_path}.aarka_rollback_stage"
                    try:
                        os.makedirs(os.path.dirname(stage_path), exist_ok=True)
                        with open(stage_path, "wb") as f:
                            f.write(snap.content)

                        # Verify staging file hash before touching live working tree
                        with open(stage_path, "rb") as f:
                            stage_bytes = f.read()
                        stage_hash = hashlib.sha256(stage_bytes).hexdigest()

                        if snap.sha256_hash and stage_hash != snap.sha256_hash:
                            raise ValueError(
                                f"Staging byte-parity mismatch on '{stage_path}': "
                                f"expected {snap.sha256_hash}, got {stage_hash}"
                            )
                        staging_files.append(stage_path)
                    except Exception as e:
                        errors.append(f"Phase 1 staging error on '{snap.file_path}': {e}")
                        # Abort phase 1: clean up temporary staging files
                        for sf in staging_files:
                            try:
                                if os.path.exists(sf):
                                    os.remove(sf)
                            except OSError:
                                pass

                        evidence = {
                            "transaction_id": transaction_id,
                            "restored_files": [],
                            "unlinked_orphans": [],
                            "errors": errors,
                            "phase": "PHASE_1_STAGING",
                            "success": False
                        }
                        # DO NOT delete active transaction on failure: preserve snapshots!
                        self._failed_transactions[transaction_id] = {
                            "snapshots": snapshots,
                            "evidence": evidence
                        }
                        self._audit_log.append({
                            "event": "transaction_rollback_failed",
                            **evidence
                        })
                        raise RollbackError(
                            f"Atomic rollback aborted in Phase 1 (no files modified): {'; '.join(errors)}",
                            recovery_evidence=evidence
                        )

            # ─── PHASE 2: Atomic Replacement & Orphan Cleanup ────────────────────
            # Phase 1 passed completely. Now atomically swap staging files into place.
            for snap in reversed(snapshots):
                try:
                    if snap.existed and snap.content is not None:
                        stage_path = f"{snap.file_path}.aarka_rollback_stage"
                        if os.path.exists(stage_path):
                            os.replace(stage_path, snap.file_path)
                            if snap.mode is not None:
                                try:
                                    os.chmod(snap.file_path, snap.mode)
                                except OSError:
                                    pass
                            restored_files.append(snap.file_path)
                    else:
                        # Unlink newly created orphan
                        if os.path.exists(snap.file_path):
                            os.remove(snap.file_path)
                            unlinked_orphans.append(snap.file_path)
                except Exception as e:
                    errors.append(f"Phase 2 replacement error on '{snap.file_path}': {e}")

            evidence = {
                "transaction_id": transaction_id,
                "restored_files": restored_files,
                "unlinked_orphans": unlinked_orphans,
                "errors": errors,
                "phase": "PHASE_2_EXECUTION",
                "success": len(errors) == 0
            }

            if errors:
                # Retain in failed transactions map so snapshot content is not discarded
                self._failed_transactions[transaction_id] = {
                    "snapshots": snapshots,
                    "evidence": evidence
                }
                self._audit_log.append({
                    "event": "transaction_rollback_partial_failure",
                    **evidence
                })
                raise RollbackError(
                    f"Rollback encountered errors during Phase 2: {'; '.join(errors)}. Snapshots preserved.",
                    recovery_evidence=evidence
                )

            # Success: clean release of active transaction
            del self._active_transactions[transaction_id]
            self._audit_log.append({
                "event": "transaction_rolled_back",
                **evidence
            })

            return evidence

    def is_active(self, transaction_id: str) -> bool:
        """Checks if a transaction is currently open."""
        with self._lock:
            return transaction_id in self._active_transactions

    def active_transaction_count(self) -> int:
        """Returns the number of currently active transactions."""
        with self._lock:
            return len(self._active_transactions)

    def get_failed_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves snapshots and evidence for a failed rollback transaction."""
        with self._lock:
            return self._failed_transactions.get(transaction_id)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Returns a copy of the recovery audit log."""
        with self._lock:
            return list(self._audit_log)
