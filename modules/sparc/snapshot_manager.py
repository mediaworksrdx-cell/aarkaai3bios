"""
Transactional Multi-File Working Tree Snapshot & Atomic Rollback Manager.
Guarantees atomic multi-file restoration, cryptographic byte-parity verification,
and orphan cleanup across SPARC swarm stages.
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
    Thread-safe, records SHA-256 hashes, verifies byte-parity upon restoration,
    and preserves detailed recovery evidence on partial failures.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active_transactions: Dict[str, List[FileSnapshot]] = {}
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
        Atomically restores all mutated files to original bytes, verifies byte parity,
        and removes newly created orphan files.
        Returns recovery evidence on success; raises RollbackError on any failure.
        """
        with self._lock:
            snapshots = self._active_transactions.get(transaction_id)
            if snapshots is None:
                raise KeyError(f"Cannot rollback: No active transaction found with ID '{transaction_id}'.")

            restored_files: List[str] = []
            unlinked_orphans: List[str] = []
            errors: List[str] = []

            for snap in reversed(snapshots):
                try:
                    if snap.existed:
                        # Restore original content
                        os.makedirs(os.path.dirname(snap.file_path), exist_ok=True)
                        with open(snap.file_path, "wb") as f:
                            if snap.content is not None:
                                f.write(snap.content)
                        if snap.mode is not None:
                            try:
                                os.chmod(snap.file_path, snap.mode)
                            except OSError:
                                pass  # Platform compatibility on Windows

                        # Parity verification: check restored SHA-256
                        if snap.content is not None and snap.sha256_hash:
                            with open(snap.file_path, "rb") as f:
                                verified_content = f.read()
                            verified_hash = hashlib.sha256(verified_content).hexdigest()
                            if verified_hash != snap.sha256_hash:
                                raise ValueError(
                                    f"Byte-parity mismatch on '{snap.file_path}': "
                                    f"expected {snap.sha256_hash}, got {verified_hash}"
                                )
                        restored_files.append(snap.file_path)
                    else:
                        # File was created during transaction; unlink orphan
                        if os.path.exists(snap.file_path):
                            os.remove(snap.file_path)
                            unlinked_orphans.append(snap.file_path)
                except Exception as e:
                    errors.append(f"Failed to restore '{snap.file_path}': {e}")

            # Always remove transaction from active list so state does not remain poisoned
            del self._active_transactions[transaction_id]

            evidence = {
                "transaction_id": transaction_id,
                "restored_files": restored_files,
                "unlinked_orphans": unlinked_orphans,
                "errors": errors,
                "success": len(errors) == 0
            }
            self._audit_log.append({
                "event": "transaction_rolled_back",
                **evidence
            })

            if errors:
                raise RollbackError(
                    f"Rollback of transaction '{transaction_id}' encountered errors: {'; '.join(errors)}",
                    recovery_evidence=evidence
                )

            return evidence

    def is_active(self, transaction_id: str) -> bool:
        """Checks if a transaction is currently open."""
        with self._lock:
            return transaction_id in self._active_transactions

    def active_transaction_count(self) -> int:
        """Returns the number of currently active transactions."""
        with self._lock:
            return len(self._active_transactions)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Returns a copy of the recovery audit log."""
        with self._lock:
            return list(self._audit_log)
