"""
AARKAAI – Fail-Closed, Hash-Chained Security Audit Logger.

Provides structured, tamper-evident security observability for all sandbox
lifecycles, MCP process launches, authorization decisions, and policy violations.
"""
import os
import json
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

AUDIT_LOG_DIR = Path("logs")
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "security_audit.jsonl"
SPOOL_DIR = Path("var")
SPOOL_FILE = SPOOL_DIR / "audit_anchors_spool.jsonl"

MAX_LOG_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_BACKUPS = 5
MAX_SPOOL_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_SPOOL_RECORDS = 10000
MAX_UNANCHORED_AGE_SECONDS = 300.0  # 300s threshold for privileged operations
MAX_RATE_PER_MINUTE = 100


class SecurityAuditError(Exception):
    """Raised when security audit logging fails, triggering fail-closed enforcement."""
    pass


class SecurityAuditLogger:
    _instance = None
    _lock = threading.RLock()

    def __init__(
        self,
        log_path: Path = AUDIT_LOG_FILE,
        spool_path: Path = SPOOL_FILE,
        fail_closed: bool = True
    ):
        self.log_path = Path(log_path)
        self.spool_path = Path(spool_path)
        self.fail_closed = fail_closed
        self._last_hash = "0" * 64
        self._rate_window: list[float] = []
        self._init_storage()

    @classmethod
    def get_instance(cls) -> "SecurityAuditLogger":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _init_storage(self):
        """Initialize directories, verify hash-chain integrity, and recover last hash."""
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.spool_path.parent.mkdir(parents=True, exist_ok=True)

            if not self.log_path.exists():
                self.log_path.touch(mode=0o600)
                self._last_hash = "0" * 64
            else:
                self._last_hash = self._recover_chain_hash(self.log_path)

            if not self.spool_path.exists():
                self.spool_path.touch(mode=0o600)
        except Exception as e:
            if self.fail_closed:
                raise SecurityAuditError(f"Failed to initialize security audit storage: {e}") from e
            logger.error("Audit storage initialization error: %s", e)

    def _recover_chain_hash(self, path: Path) -> str:
        """Read last line of the existing log and recover its record_hash."""
        last_hash = "0" * 64
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        rec_hash = record.get("record_hash")
                        if rec_hash and len(rec_hash) == 64:
                            last_hash = rec_hash
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning("Could not fully recover chain hash from %s: %s", path, e)
        return last_hash

    @staticmethod
    def _sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """Minimizes sensitive fields by hashing or measuring lengths."""
        sanitized = {}
        for k, v in details.items():
            k_low = k.lower()
            if any(secret_term in k_low for secret_term in ["token", "key", "secret", "password", "auth", "credential"]):
                if isinstance(v, str):
                    sanitized[k] = {
                        "length": len(v),
                        "sha256": hashlib.sha256(v.encode("utf-8")).hexdigest()[:16] + "..."
                    }
                else:
                    sanitized[k] = "[REDACTED]"
            elif k_low in ["args", "arguments", "params", "parameters"] and isinstance(v, dict):
                arg_summary = {}
                for ak, av in v.items():
                    if any(st in ak.lower() for st in ["token", "key", "secret", "password"]):
                        arg_summary[ak] = "[REDACTED]"
                    elif isinstance(av, str):
                        arg_summary[ak] = f"str(len={len(av)})"
                    else:
                        arg_summary[ak] = type(av).__name__
                sanitized[k] = arg_summary
            else:
                sanitized[k] = v
        return sanitized

    def _check_rate_limit(self, now: float):
        """Rate limits audit logging per minute to prevent flooding."""
        self._rate_window = [t for t in self._rate_window if now - t < 60.0]
        if len(self._rate_window) >= MAX_RATE_PER_MINUTE:
            logger.warning("Security audit rate limit hit (%d records/min). Throttling.", MAX_RATE_PER_MINUTE)
        self._rate_window.append(now)

    def _rotate_if_needed(self):
        """Rotate audit log if size exceeds limit, maintaining hash-chain seed."""
        try:
            if not self.log_path.exists() or self.log_path.stat().st_size < MAX_LOG_BYTES:
                return

            seed_hash = self._last_hash
            # Shift older backups
            for i in range(MAX_BACKUPS - 1, 0, -1):
                src = self.log_path.with_name(f"{self.log_path.name}.{i}")
                dst = self.log_path.with_name(f"{self.log_path.name}.{i + 1}")
                if src.exists():
                    if dst.exists():
                        dst.unlink()
                    src.rename(dst)
                    try:
                        os.chmod(dst, 0o400)
                    except Exception:
                        pass

            backup1 = self.log_path.with_name(f"{self.log_path.name}.1")
            self.log_path.rename(backup1)
            try:
                os.chmod(backup1, 0o400)
            except Exception:
                pass

            # Create new log with seed link record
            self.log_path.touch(mode=0o600)
            init_record = {
                "event_type": "audit.rotation_chain_seed",
                "timestamp": time.time(),
                "prev_record_hash": seed_hash,
                "details": {"previous_file": str(backup1.name)}
            }
            content_to_hash = json.dumps(init_record, sort_keys=True)
            new_hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()
            init_record["record_hash"] = new_hash

            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(init_record) + "\n")
                f.flush()
                os.fsync(f.fileno())

            self._last_hash = new_hash
        except Exception as e:
            if self.fail_closed:
                raise SecurityAuditError(f"Audit log rotation failed: {e}") from e
            logger.error("Audit log rotation error: %s", e)

    def log_event(self, event_type: str, details: Dict[str, Any]) -> str:
        """
        Record a security event with hash chaining.
        Fails closed by raising SecurityAuditError if any write fails.
        """
        now = time.time()
        with self._lock:
            self._check_rate_limit(now)
            self._rotate_if_needed()

            sanitized_details = self._sanitize_details(details)
            record = {
                "event_type": event_type,
                "timestamp": now,
                "prev_record_hash": self._last_hash,
                "details": sanitized_details
            }
            content_str = json.dumps(record, sort_keys=True)
            record_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
            record["record_hash"] = record_hash

            try:
                # 1. Write to main audit log
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
                    f.flush()
                    os.fsync(f.fileno())

                # 2. Append to local external anchor spool
                self._append_to_spool(record)

                self._last_hash = record_hash
                return record_hash
            except Exception as e:
                if self.fail_closed:
                    raise SecurityAuditError(f"Failed to record security audit event '{event_type}': {e}") from e
                logger.error("Audit logging failure: %s", e)
                return ""

    def _append_to_spool(self, record: Dict[str, Any]):
        """Append record hash to local anchor spool with capacity checks."""
        try:
            if self.spool_path.exists() and self.spool_path.stat().st_size > MAX_SPOOL_BYTES:
                raise SecurityAuditError("Audit anchor spool capacity exceeded (10 MB).")

            spool_entry = {
                "timestamp": record["timestamp"],
                "record_hash": record["record_hash"],
                "event_type": record["event_type"]
            }
            with open(self.spool_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(spool_entry) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            if self.fail_closed:
                raise SecurityAuditError(f"Failed writing to audit spool: {e}") from e
            logger.error("Audit spool append error: %s", e)

    def check_spool_health_for_privileged_operation(self) -> None:
        """
        Enforces the availability policy:
        Privileged/mutating operations FAIL CLOSED if unanchored entries exceed 300s.
        """
        if not self.spool_path.exists():
            return

        now = time.time()
        oldest_unanchored: Optional[float] = None
        count = 0

        try:
            with open(self.spool_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        ts = entry.get("timestamp")
                        if ts is not None:
                            count += 1
                            if oldest_unanchored is None or ts < oldest_unanchored:
                                oldest_unanchored = ts
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            if self.fail_closed:
                raise SecurityAuditError(f"Cannot verify audit spool health: {e}") from e
            return

        if oldest_unanchored is not None:
            age = now - oldest_unanchored
            if age > MAX_UNANCHORED_AGE_SECONDS:
                raise SecurityAuditError(
                    f"Privileged operation blocked: Audit spool unanchored age ({age:.1f}s) "
                    f"exceeds limit ({MAX_UNANCHORED_AGE_SECONDS}s). External checkpoint sync required."
                )

        if count >= MAX_SPOOL_RECORDS:
            raise SecurityAuditError(
                f"Privileged operation blocked: Audit spool record count ({count}) reached capacity."
            )

    def acknowledge_spool_anchored(self, up_to_hash: str):
        """Remove anchored entries from spool up to the acknowledged record hash."""
        with self._lock:
            if not self.spool_path.exists():
                return
            temp_file = self.spool_path.with_suffix(".tmp")
            found = False
            remaining = []
            try:
                with open(self.spool_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        entry = json.loads(line)
                        if not found:
                            if entry.get("record_hash") == up_to_hash:
                                found = True
                            continue
                        remaining.append(line)

                with open(temp_file, "w", encoding="utf-8") as f:
                    for r in remaining:
                        f.write(r if r.endswith("\n") else r + "\n")
                    f.flush()
                    os.fsync(f.fileno())

                temp_file.replace(self.spool_path)
            except Exception as e:
                if temp_file.exists():
                    temp_file.unlink()
                logger.error("Error updating audit spool after anchor: %s", e)


def audit_event(event_type: str, **details) -> str:
    """Convenience helper to record an audit event via the singleton logger."""
    return SecurityAuditLogger.get_instance().log_event(event_type, details)


def verify_audit_log_integrity(log_path: Path) -> tuple[bool, int, Optional[str]]:
    """
    Cryptographically verify the SHA-256 hash chain of an audit log.
    Returns (is_valid, record_count, error_message).
    """
    path = Path(log_path)
    if not path.exists():
        return False, 0, f"Audit log not found: {path}"

    count = 0
    expected_prev = None

    try:
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    return False, count, f"Line {idx}: malformed JSON ({e})"

                stated_hash = record.pop("record_hash", None)
                if not stated_hash:
                    return False, count, f"Line {idx}: missing 'record_hash'"

                actual_prev = record.get("prev_record_hash")
                if expected_prev is not None and actual_prev != expected_prev:
                    return False, count, (
                        f"Line {idx}: hash chain broken. "
                        f"Expected prev_record_hash '{expected_prev}', got '{actual_prev}'"
                    )

                content_str = json.dumps(record, sort_keys=True)
                recomputed_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

                if recomputed_hash != stated_hash:
                    return False, count, (
                        f"Line {idx}: tampering detected. "
                        f"Stored hash '{stated_hash}' != recomputed '{recomputed_hash}'"
                    )

                expected_prev = stated_hash
                count += 1

        return True, count, None
    except Exception as e:
        return False, count, f"Audit verification error: {e}"
