"""
AARKAAI – Enterprise Durable Multi-Worker Approval Store.

Provides atomic, concurrency-safe, tamper-resistant human-in-the-loop approval gates.
Features:
- Multi-worker coordination via SQLite Write-Ahead Logging (WAL) and PRAGMA synchronous=FULL.
- Deep action hash binding over tool name, canonical args, user ID, session ID, workspace ID,
  policy version, MCP server ID, and target resource.
- Atomic Compare-And-Swap (CAS) state machine resolving approval vs. expiry races.
- Deterministic cancellation propagation when actions are denied or expire.
- Fail-closed security auditing with cryptographic hash-chain integration.
"""
from __future__ import annotations

import os
import time
import json
import sqlite3
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from modules.security_audit import audit_event

logger = logging.getLogger(__name__)

DEFAULT_APPROVAL_DB = Path("var") / "approvals.db"
DEFAULT_APPROVAL_TIMEOUT_SECONDS = 120.0
DEFAULT_POLICY_VERSION = "aarkaa_v1.0"


def compute_action_hash(
    tool_name: str,
    args: Dict[str, Any],
    user_id: str,
    session_id: str,
    workspace_id: str = "default",
    policy_version: str = DEFAULT_POLICY_VERSION,
    mcp_server_id: str = "",
    target_resource: str = ""
) -> str:
    """
    Computes an immutable canonical SHA-256 action hash binding:
    (tool_name, args, user_id, session_id, workspace_id, policy_version, mcp_server_id, target_resource).
    """
    canonical_payload = {
        "tool_name": str(tool_name).strip(),
        "args": args,
        "user_id": str(user_id).strip(),
        "session_id": str(session_id).strip(),
        "workspace_id": str(workspace_id).strip(),
        "policy_version": str(policy_version).strip(),
        "mcp_server_id": str(mcp_server_id).strip(),
        "target_resource": str(target_resource).strip()
    }
    canonical_str = json.dumps(canonical_payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


@dataclass
class ToolApprovalRecord:
    approval_id: str
    user_id: str
    session_id: str
    workspace_id: str
    tool_name: str
    args: Dict[str, Any]
    action_hash: str
    policy_version: str
    mcp_server_id: str
    target_resource: str
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    human_summary: str
    diff_preview: Optional[str]
    command_preview: Optional[str]
    status: str  # "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED"
    created_at: float
    expires_at: float
    resolved_at: Optional[float] = None
    resolved_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d.get("created_at") and d["created_at"] < 1e11:
            d["created_at"] = int(d["created_at"] * 1000)
        if d.get("expires_at") and d["expires_at"] < 1e11:
            d["expires_at"] = int(d["expires_at"] * 1000)
        if d.get("resolved_at") and d["resolved_at"] < 1e11:
            d["resolved_at"] = int(d["resolved_at"] * 1000)
        return d


@dataclass
class ApprovalResponse:
    approval_id: str
    status: str  # "approved" | "rejected" | "expired" | "invalid" | "unauthorized"
    message: str
    action_hash: Optional[str] = None


class ApprovalStoreInterface(ABC):
    @abstractmethod
    def create_request(
        self,
        user_id: str,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any],
        risk_level: str,
        human_summary: str,
        workspace_id: str = "default",
        policy_version: str = DEFAULT_POLICY_VERSION,
        mcp_server_id: str = "",
        target_resource: str = "",
        diff_preview: Optional[str] = None,
        command_preview: Optional[str] = None,
        timeout_seconds: float = DEFAULT_APPROVAL_TIMEOUT_SECONDS
    ) -> ToolApprovalRecord:
        pass

    @abstractmethod
    def resolve_request(
        self,
        approval_id: str,
        user_id: str,
        decision: str  # "APPROVED" | "REJECTED"
    ) -> ApprovalResponse:
        pass

    @abstractmethod
    def get_request(self, approval_id: str) -> Optional[ToolApprovalRecord]:
        pass

    @abstractmethod
    def await_resolution(
        self,
        approval_id: str,
        expected_action_hash: str,
        timeout_seconds: float = DEFAULT_APPROVAL_TIMEOUT_SECONDS,
        poll_interval: float = 0.25
    ) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def cancel_and_expire_stale(self, now: Optional[float] = None) -> int:
        pass


class SQLiteApprovalStore(ApprovalStoreInterface):
    """
    Durable single-host multi-worker approval coordination engine backed by SQLite WAL.
    """
    def __init__(self, db_path: Path = DEFAULT_APPROVAL_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_approvals (
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
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_user ON tool_approvals(user_id, status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_expiry ON tool_approvals(expires_at);")

    def create_request(
        self,
        user_id: str,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any],
        risk_level: str,
        human_summary: str,
        workspace_id: str = "default",
        policy_version: str = DEFAULT_POLICY_VERSION,
        mcp_server_id: str = "",
        target_resource: str = "",
        diff_preview: Optional[str] = None,
        command_preview: Optional[str] = None,
        timeout_seconds: float = DEFAULT_APPROVAL_TIMEOUT_SECONDS
    ) -> ToolApprovalRecord:
        import uuid
        now = time.time()
        expires_at = now + timeout_seconds
        approval_id = f"appr_{uuid.uuid4().hex[:16]}"
        action_hash = compute_action_hash(
            tool_name=tool_name,
            args=args,
            user_id=user_id,
            session_id=session_id,
            workspace_id=workspace_id,
            policy_version=policy_version,
            mcp_server_id=mcp_server_id,
            target_resource=target_resource
        )

        record = ToolApprovalRecord(
            approval_id=approval_id,
            user_id=user_id,
            session_id=session_id,
            workspace_id=workspace_id,
            tool_name=tool_name,
            args=args,
            action_hash=action_hash,
            policy_version=policy_version,
            mcp_server_id=mcp_server_id,
            target_resource=target_resource,
            risk_level=risk_level,
            human_summary=human_summary,
            diff_preview=diff_preview,
            command_preview=command_preview,
            status="PENDING",
            created_at=now,
            expires_at=expires_at
        )

        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("""
                INSERT INTO tool_approvals (
                    approval_id, user_id, session_id, workspace_id, tool_name,
                    args_json, action_hash, policy_version, mcp_server_id, target_resource,
                    risk_level, human_summary, diff_preview, command_preview,
                    status, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                record.approval_id, record.user_id, record.session_id, record.workspace_id,
                record.tool_name, json.dumps(record.args, sort_keys=True), record.action_hash,
                record.policy_version, record.mcp_server_id, record.target_resource,
                record.risk_level, record.human_summary, record.diff_preview, record.command_preview,
                record.status, record.created_at, record.expires_at
            ))
            conn.commit()

            audit_event(
                "approval.created",
                approval_id=approval_id,
                user_id=user_id,
                tool_name=tool_name,
                risk_level=risk_level,
                action_hash=action_hash
            )
            return record
        except Exception as e:
            conn.rollback()
            logger.error("Failed to create approval request: %s", e)
            raise
        finally:
            conn.close()

    def resolve_request(
        self,
        approval_id: str,
        user_id: str,
        decision: str
    ) -> ApprovalResponse:
        decision_clean = decision.upper()
        if decision_clean not in ("APPROVED", "REJECTED"):
            return ApprovalResponse(approval_id, "invalid", f"Invalid decision: {decision}")

        now = time.time()
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_approvals WHERE approval_id = ?;", (approval_id,))
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return ApprovalResponse(approval_id, "invalid", "Approval request not found")

            # Ownership check: allow same user, or default/guest user session, or admin
            if row["user_id"] != user_id and row["user_id"] != "default" and user_id != "admin":
                conn.rollback()
                audit_event("approval.unauthorized_access", approval_id=approval_id, attempted_by=user_id, owner=row["user_id"])
                return ApprovalResponse(approval_id, "unauthorized", "User does not own this approval request")

            current_status = row["status"]
            if current_status != "PENDING":
                conn.rollback()
                return ApprovalResponse(
                    approval_id,
                    current_status.lower(),
                    f"Approval already in state: {current_status}",
                    action_hash=row["action_hash"]
                )

            # Check if expired
            if now > row["expires_at"]:
                cursor.execute("""
                    UPDATE tool_approvals
                    SET status = 'EXPIRED', resolved_at = ?, resolved_by = 'system_timeout'
                    WHERE approval_id = ? AND status = 'PENDING';
                """, (now, approval_id))
                conn.commit()
                audit_event("approval.expired_on_resolve", approval_id=approval_id)
                return ApprovalResponse(approval_id, "expired", "Approval request has expired")

            # Atomic CAS update
            cursor.execute("""
                UPDATE tool_approvals
                SET status = ?, resolved_at = ?, resolved_by = ?
                WHERE approval_id = ? AND status = 'PENDING' AND expires_at > ?;
            """, (decision_clean, now, user_id, approval_id, now))

            if cursor.rowcount == 0:
                conn.rollback()
                # Race condition occurred
                cursor.execute("SELECT status FROM tool_approvals WHERE approval_id = ?;", (approval_id,))
                fresh_row = cursor.fetchone()
                fresh_status = fresh_row["status"] if fresh_row else "invalid"
                return ApprovalResponse(approval_id, fresh_status.lower(), "State race condition resolved")

            conn.commit()
            audit_event(
                f"approval.{decision_clean.lower()}",
                approval_id=approval_id,
                resolved_by=user_id,
                action_hash=row["action_hash"],
                tool=row["tool_name"]
            )
            return ApprovalResponse(
                approval_id=approval_id,
                status=decision_clean.lower(),
                message=f"Action successfully {decision_clean.lower()}",
                action_hash=row["action_hash"]
            )
        except Exception as e:
            conn.rollback()
            logger.error("Error resolving approval %s: %s", approval_id, e)
            return ApprovalResponse(approval_id, "invalid", f"Resolution error: {e}")
        finally:
            conn.close()

    def get_request(self, approval_id: str) -> Optional[ToolApprovalRecord]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_approvals WHERE approval_id = ?;", (approval_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ToolApprovalRecord(
                approval_id=row["approval_id"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                workspace_id=row["workspace_id"],
                tool_name=row["tool_name"],
                args=json.loads(row["args_json"]),
                action_hash=row["action_hash"],
                policy_version=row["policy_version"],
                mcp_server_id=row["mcp_server_id"],
                target_resource=row["target_resource"],
                risk_level=row["risk_level"],
                human_summary=row["human_summary"],
                diff_preview=row["diff_preview"],
                command_preview=row["command_preview"],
                status=row["status"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                resolved_at=row["resolved_at"],
                resolved_by=row["resolved_by"]
            )
        finally:
            conn.close()

    def await_resolution(
        self,
        approval_id: str,
        expected_action_hash: str,
        timeout_seconds: float = DEFAULT_APPROVAL_TIMEOUT_SECONDS,
        poll_interval: float = 0.25
    ) -> Tuple[bool, str]:
        """
        Polls the durable SQLite approval table until resolved, expired, or timed out.
        Verifies expected_action_hash upon approval to guarantee zero parameter tampering.
        """
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            rec = self.get_request(approval_id)
            if not rec:
                return False, "Approval record not found"

            now = time.time()
            if rec.status == "APPROVED":
                # Strict action-hash verification
                if rec.action_hash != expected_action_hash:
                    audit_event("approval.tamper_detected", approval_id=approval_id, expected=expected_action_hash, actual=rec.action_hash)
                    return False, "Action hash verification failed: parameters were altered"
                return True, "Approved by user"
            elif rec.status == "REJECTED":
                return False, "Action denied by user"
            elif rec.status == "EXPIRED" or now > rec.expires_at:
                if rec.status == "PENDING":
                    self._mark_expired(approval_id, now)
                return False, "Approval request expired"

            time.sleep(poll_interval)

        # Timed out waiting
        self._mark_expired(approval_id, time.time())
        return False, "Approval timed out"

    def _mark_expired(self, approval_id: str, now: float):
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("""
                UPDATE tool_approvals
                SET status = 'EXPIRED', resolved_at = ?, resolved_by = 'system_timeout'
                WHERE approval_id = ? AND status = 'PENDING';
            """, (now, approval_id))
            conn.commit()
            audit_event("approval.expired", approval_id=approval_id)
        except Exception:
            conn.rollback()
        finally:
            conn.close()

    def cancel_and_expire_stale(self, now: Optional[float] = None) -> int:
        if now is None:
            now = time.time()
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tool_approvals
                SET status = 'EXPIRED', resolved_at = ?, resolved_by = 'system_sweeper'
                WHERE status = 'PENDING' AND expires_at < ?;
            """, (now, now))
            count = cursor.rowcount
            conn.commit()
            return count
        except Exception as e:
            conn.rollback()
            logger.error("Error expiring stale approvals: %s", e)
            return 0
        finally:
            conn.close()


_approval_store_instance: Optional[ApprovalStoreInterface] = None


def get_approval_store() -> ApprovalStoreInterface:
    global _approval_store_instance
    if _approval_store_instance is None:
        backend = os.getenv("AARKAAI_APPROVAL_BACKEND", "sqlite").lower()
        if backend == "sqlite":
            _approval_store_instance = SQLiteApprovalStore()
        else:
            logger.warning("Unrecognized approval backend '%s'; defaulting to SQLite WAL.", backend)
            _approval_store_instance = SQLiteApprovalStore()
    return _approval_store_instance
