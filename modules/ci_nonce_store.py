"""
AARKAAI – Durable, Concurrency-Safe SQLite WAL Nonce Store & CI Token Verifier.

Enforces replay-resistant, cryptographically sealed approval tokens for headless CI environments.
Uses SQLite with Write-Ahead Logging (WAL) and PRAGMA synchronous=FULL for crash durability.
"""
import os
import time
import hmac
import json
import base64
import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_NONCE_DB = Path("var") / "ci_nonces.db"
DEFAULT_AUTH_WINDOW_SECONDS = 300.0  # 300s token validity
DEFAULT_RETENTION_SECONDS = 600.0    # 600s storage GC retention
CLOCK_SKEW_TOLERANCE_SECONDS = 30.0

PERMITTED_CI_SCOPES = {
    "non-destructive-benchmarks",
    "unit-testing",
    "read-only-evaluation"
}

FORBIDDEN_OPERATIONS = {
    "deployment",
    "deploy",
    "file_delete",
    "delete_file",
    "system_delete",
    "network_egress",
    "credential_access"
}


class CINonceStore:
    def __init__(self, db_path: Path = DEFAULT_NONCE_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consumed_nonces (
                    nonce TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    consumed_at REAL NOT NULL,
                    PRIMARY KEY (nonce, commit_sha)
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_consumed_at ON consumed_nonces(consumed_at);")

    def consume_nonce(self, nonce: str, commit_sha: str, now: Optional[float] = None) -> bool:
        """
        Atomically records a nonce under write-serialized transaction (BEGIN IMMEDIATE).
        Returns True if the nonce was fresh and successfully consumed.
        Returns False if the nonce was already consumed (replay detected).
        """
        if now is None:
            now = time.time()

        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT consumed_at FROM consumed_nonces WHERE nonce = ? AND commit_sha = ?;",
                (nonce, commit_sha)
            )
            if cursor.fetchone() is not None:
                conn.rollback()
                return False  # Replay detected

            cursor.execute(
                "INSERT INTO consumed_nonces (nonce, commit_sha, consumed_at) VALUES (?, ?, ?);",
                (nonce, commit_sha, now)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        except Exception as e:
            conn.rollback()
            logger.error("Error in consume_nonce: %s", e)
            raise
        finally:
            conn.close()

    def cleanup_expired_nonces(self, now: Optional[float] = None, retention_seconds: float = DEFAULT_RETENTION_SECONDS) -> int:
        """Purge nonces older than retention_seconds (storage maintenance)."""
        if now is None:
            now = time.time()
        cutoff = now - retention_seconds
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM consumed_nonces WHERE consumed_at < ?;", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception as e:
            conn.rollback()
            logger.error("Error during nonce cleanup: %s", e)
            return 0
        finally:
            conn.close()


def generate_ci_token(
    signing_key: str,
    repo: str,
    commit_sha: str,
    workflow_run_id: str,
    job_id: str,
    tool_scope: str,
    kid: str = "k1",
    env: str = "staging-ci",
    expires_in_seconds: float = DEFAULT_AUTH_WINDOW_SECONDS,
    now: Optional[float] = None
) -> str:
    """Generate a cryptographically sealed HMAC-SHA256 CI approval token."""
    if now is None:
        now = time.time()

    nonce = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
    payload = {
        "iss": "aarkaa-auth-service",
        "aud": "aarkaa-code-mode",
        "kid": kid,
        "repo": repo,
        "commit_sha": commit_sha,
        "workflow_run_id": workflow_run_id,
        "job_id": job_id,
        "tool_scope": tool_scope,
        "env": env,
        "exp": now + expires_in_seconds,
        "nbf": now,
        "nonce": nonce
    }
    header = {"alg": "HS256", "typ": "JWT", "kid": kid}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header, sort_keys=True).encode("utf-8")).decode("utf-8").rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode("utf-8")).decode("utf-8").rstrip("=")
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(signing_key.encode("utf-8"), message, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_ci_approval_token(
    token: str,
    signing_keys: Dict[str, str],  # {"k1": "primary_key", "k0": "old_key"}
    expected_repo: str,
    expected_commit: str,
    nonce_store: CINonceStore,
    now: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Constant-time verification of CI token:
    1. Signature & Key ID validation
    2. Expiry & clock skew checks
    3. Scope & anti-escalation enforcement
    4. Durable single-use nonce consumption
    """
    if now is None:
        now = time.time()

    parts = token.split(".")
    if len(parts) != 3:
        return False, "Malformed token structure"

    header_b64, payload_b64, sig_b64 = parts

    try:
        def b64_decode(s):
            padding = 4 - (len(s) % 4)
            if padding and padding != 4:
                s += "=" * padding
            return base64.urlsafe_b64decode(s.encode("utf-8"))

        header = json.loads(b64_decode(header_b64).decode("utf-8"))
        payload = json.loads(b64_decode(payload_b64).decode("utf-8"))
        signature = b64_decode(sig_b64)
    except Exception as e:
        return False, f"Token decode failed: {e}"

    # 1. Key ID lookup
    kid = header.get("kid", "k1")
    key = signing_keys.get(kid)
    if not key:
        return False, f"Unknown or untrusted key ID: {kid}"

    # 2. Constant-time signature check
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(key.encode("utf-8"), message, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_sig):
        return False, "Signature verification failed"

    # 3. Claims validation
    if payload.get("iss") != "aarkaa-auth-service" or payload.get("aud") != "aarkaa-code-mode":
        return False, "Invalid issuer or audience"

    if payload.get("repo") != expected_repo:
        return False, f"Repository mismatch: {payload.get('repo')} != {expected_repo}"

    if payload.get("commit_sha") != expected_commit:
        return False, f"Commit SHA mismatch: {payload.get('commit_sha')} != {expected_commit}"

    # 4. Expiry & Clock Skew
    exp = payload.get("exp", 0)
    nbf = payload.get("nbf", 0)
    if now > (exp + CLOCK_SKEW_TOLERANCE_SECONDS):
        return False, "Token expired"
    if now < (nbf - CLOCK_SKEW_TOLERANCE_SECONDS):
        return False, "Token not yet valid (nbf)"

    # 5. Scope escalation check
    scope = payload.get("tool_scope", "")
    if scope not in PERMITTED_CI_SCOPES:
        return False, f"Scope '{scope}' is not permitted for CI automated approval"

    if any(forbid in scope.lower() for forbid in FORBIDDEN_OPERATIONS):
        return False, "Scope requests forbidden operation (deployment/destructive/network)"

    # 6. Atomic Nonce Consumption
    nonce = payload.get("nonce")
    if not nonce or len(nonce) < 16:
        return False, "Missing or invalid nonce"

    consumed = nonce_store.consume_nonce(nonce, expected_commit, now=now)
    if not consumed:
        return False, "Token replay detected: nonce already consumed"

    return True, "Token verified and consumed"
