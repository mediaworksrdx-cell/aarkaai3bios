"""
Hardened Cryptographic Capability Gateway for Aarka Backend.
Enforces HMAC-SHA256 token authorization, action-scoped permissions, and anti-TOCTOU containment.
"""

import hmac
import hashlib
import os
import re
import time
import urllib.parse
from typing import Optional


class CapabilityAction:
    READ = 0x01
    WRITE = 0x02
    EXECUTE = 0x04


class HardenedCapabilityGateway:
    """
    Validates cryptographic capability tokens for file interactions and ensures
    strict directory containment via canonical realpath resolution (Rule 8).
    """

    def __init__(self, workspace_root: str, signing_key: Optional[bytes] = None) -> None:
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
        # Generate persistent or randomized session signing secret
        self._signing_key = signing_key or os.urandom(32)

    def mint_token(self, relative_path: str, actions: int, ttl_seconds: int = 300) -> str:
        """
        Mints an HMAC-SHA256 signed capability token for a specific workspace path and action mask.
        """
        canonical_path = self.resolve_canonical_path(relative_path)
        rel_token_path = os.path.relpath(canonical_path, self.workspace_root).replace("\\", "/")
        expires_at = int(time.time()) + ttl_seconds
        payload = f"{rel_token_path}:{actions}:{expires_at}"
        sig = hmac.new(self._signing_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{payload}:{sig}"

    def verify_token(self, token: str, required_action: int) -> str:
        """
        Validates token authenticity, expiration, and requested action bitmask.
        Returns the absolute canonical path on success, or raises SecurityError.
        """
        if not token or "\0" in token:
            raise PermissionError("SECURITY ALERT: Invalid or null-injected capability token.")

        parts = token.split(":")
        if len(parts) != 4:
            raise PermissionError("SECURITY ALERT: Malformed capability token structure.")

        rel_path, actions_str, expires_at_str, signature = parts

        try:
            actions = int(actions_str)
            expires_at = int(expires_at_str)
        except ValueError as e:
            raise PermissionError("SECURITY ALERT: Invalid token numeric fields.") from e

        # 1. TTL Expiration Check
        if time.time() > expires_at:
            raise TimeoutError("SECURITY ALERT: Capability token has expired.")

        # 2. Cryptographic HMAC Signature Verification
        expected_payload = f"{rel_path}:{actions}:{expires_at}"
        expected_sig = hmac.new(self._signing_key, expected_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise PermissionError("SECURITY ALERT: Capability token signature mismatch or forgery detected.")

        # 3. Action Bitmask Check
        if (actions & required_action) != required_action:
            raise PermissionError(
                f"SECURITY ALERT: Insufficient capability permissions. Required: {required_action}, Granted: {actions}"
            )

        # 4. Anti-TOCTOU Canonical Path Resolution & Boundary Check
        return self.resolve_canonical_path(rel_path)

    def resolve_canonical_path(self, target_path: str) -> str:
        """
        Dereferences path via os.path.realpath and verifies containment within workspace root.
        Mitigates symlink traversal, URL-encoding, tilde expansion, and relative breakout attacks (Rule 8).
        """
        if not target_path or "\0" in target_path:
            raise PermissionError("SECURITY ALERT: Null byte or empty string detected in file path.")

        # Decode URL-encoded path components (%2e%2e, %2f, etc.)
        decoded_path = urllib.parse.unquote(target_path)
        while urllib.parse.unquote(decoded_path) != decoded_path:
            decoded_path = urllib.parse.unquote(decoded_path)

        # Expand home directory reference (~)
        if decoded_path.startswith("~"):
            decoded_path = os.path.expanduser(decoded_path)

        # Normalize separators
        norm_input = decoded_path.replace("\\", "/")

        # Prevent parent directory traversal patterns (.. or repetitive dot sequences)
        path_segments = norm_input.split("/")
        for segment in path_segments:
            if re.match(r"^\.{2,}$", segment):
                raise PermissionError(f"SECURITY ALERT: Path traversal attempted via '{segment}' in '{target_path}'.")

        # Check for cross-platform drive letter traversal on POSIX
        if os.name != "nt" and re.match(r"^[a-zA-Z]:", decoded_path):
            raise PermissionError(
                f"SECURITY ALERT: Windows drive path '{target_path}' escapes POSIX workspace root."
            )

        # Resolve full canonical path
        if not os.path.isabs(decoded_path):
            full_path = os.path.join(self.workspace_root, decoded_path)
        else:
            full_path = decoded_path

        canonical = os.path.realpath(full_path)

        # Verify common prefix
        common = os.path.commonpath([self.workspace_root, canonical])
        if common != self.workspace_root:
            raise PermissionError(
                f"SECURITY ALERT: Workspace containment violation. Target '{canonical}' escapes '{self.workspace_root}'."
            )

        return canonical
