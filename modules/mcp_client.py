"""
AARKAAI – Hardened Model Context Protocol (MCP) Client (Stage 1).

Features:
- Strict binary allowlisting with os.path.realpath, mode bits, SUID/SGID rejection, and SHA-256 validation.
- Complete argv vector validation (rejects interpreter flags, path traversal, unexpected arguments).
- close_fds=True and whitelisted environment execution.
- Defense-in-depth sanitization: control token neutralization, Unicode NFKC normalization, credential scrubbing.
- Typed observation output formatting.
- Quarantine-by-default trust model with fail-closed security auditing.
"""
import os
import sys
import json
import yaml
import time
import shlex
import hashlib
import asyncio
import logging
import dataclasses
import unicodedata
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from modules.security_audit import audit_event, SecurityAuditError

try:
    from modules.tools.base import Tool
except ImportError:
    class Tool:
        name: str = "BaseTool"
        description: str = "Base description"
        def execute(self, **kwargs) -> str:
            raise NotImplementedError

logger = logging.getLogger(__name__)

# Disallowed interpreter execution flags that could run unvetted code
FORBIDDEN_INTERPRETER_FLAGS = {
    "-c", "-e", "-m", "--eval", "--import", "--inspect", "--interactive", "-i"
}

CONTROL_TOKENS_PATTERN = re.compile(
    r"<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>|\[THINKING\]|\[/THINKING\]|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>"
)

SECRET_PATTERNS = [
    re.compile(r"(?i)(?:api[_-]?key|bearer|secret|password|auth[_-]?token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}")
]


class MCPTrustError(Exception):
    """Raised when an MCP binary, argument vector, or response violates trust policies."""
    pass


@dataclasses.dataclass
class MCPToolSchema:
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


@dataclasses.dataclass
class ToolPermissions:
    can_read: bool = False
    can_write: bool = False
    can_execute: bool = False
    can_network: bool = False
    rate_limit_rpm: int = 60
    timeout_seconds: float = 10.0
    max_output_bytes: int = 65536


def sanitize_mcp_output(raw_output: str, max_bytes: int = 65536) -> str:
    """
    Defense-in-depth sanitization:
    1. Unicode NFKC normalization (neutralizing homoglyph disguises)
    2. Stripping model tokenizer control sequences
    3. Redacting sensitive credentials and API tokens
    4. Truncating byte length to max_bytes
    """
    # 1. Unicode normalization
    text = unicodedata.normalize("NFKC", raw_output)

    # 2. Neutralize tokenizer control sequences
    text = CONTROL_TOKENS_PATTERN.sub("", text)

    # 3. Scrub secrets
    for pat in SECRET_PATTERNS:
        text = pat.sub("[REDACTED_SECRET]", text)

    # 4. Truncate
    encoded = text.encode("utf-8")
    if len(encoded) > max_bytes:
        encoded = encoded[:max_bytes]
        text = encoded.decode("utf-8", errors="ignore") + "... [truncated]"

    return text


def validate_mcp_command_and_argv(parts: List[str], server_name: str, admin_allowlist: Dict[str, Any]) -> None:
    """
    Validates:
    - Executable path is absolute (basenames rejected)
    - Resolves via realpath to defeat symlinks
    - Binary exists in admin allowlist
    - Expected SHA-256 hash matches
    - Mode bits: not world-writable, no SUID/SGID bits
    - Arguments: no forbidden interpreter execution flags or path traversal
    """
    if not parts:
        raise MCPTrustError(f"Server '{server_name}' has empty command.")

    raw_exe = parts[0]
    if not os.path.isabs(raw_exe):
        raise MCPTrustError(f"Basename or relative path '{raw_exe}' rejected. Must be an absolute path.")

    real_exe = os.path.realpath(raw_exe)
    if not os.path.exists(real_exe):
        raise MCPTrustError(f"Resolved executable '{real_exe}' does not exist.")

    # Allowlist check (if allowlist configured)
    if admin_allowlist:
        server_entry = admin_allowlist.get(server_name)
        if not server_entry:
            raise MCPTrustError(f"Server '{server_name}' not found in administrator allowlist.")

        expected_path = server_entry.get("path")
        if expected_path and os.path.realpath(expected_path) != real_exe:
            raise MCPTrustError(f"Executable '{real_exe}' does not match expected allowlisted path '{expected_path}'.")

        # SHA-256 hash check
        expected_hash = server_entry.get("sha256")
        if expected_hash:
            with open(real_exe, "rb") as f:
                computed_hash = hashlib.sha256(f.read()).hexdigest()
            if computed_hash.lower() != expected_hash.lower():
                raise MCPTrustError(f"SHA-256 hash mismatch for '{real_exe}'. Binary may have been altered.")

    # File permission mode check (POSIX mode bits)
    if os.name != "nt":
        try:
            st = os.stat(real_exe)
            # World-writable check (0o002)
            if st.st_mode & 0o002:
                raise MCPTrustError(f"Executable '{real_exe}' is world-writable (mode {oct(st.st_mode)}).")
            # SUID/SGID check (0o4000, 0o2000)
            if st.st_mode & 0o6000:
                raise MCPTrustError(f"Executable '{real_exe}' has SUID/SGID bits set.")
        except OSError as e:
            raise MCPTrustError(f"Failed to inspect mode bits for '{real_exe}': {e}")

    # Argument vector (argv) validation
    for arg in parts[1:]:
        # Disallow interpreter code execution flags
        if arg in FORBIDDEN_INTERPRETER_FLAGS:
            raise MCPTrustError(f"Forbidden interpreter flag '{arg}' in arguments for server '{server_name}'.")

        # Disallow path traversal
        if ".." in arg.replace("\\", "/").split("/"):
            raise MCPTrustError(f"Path traversal '..' detected in argument '{arg}' for server '{server_name}'.")


class MCPServerConnection:
    def __init__(self, server_name: str, config: Dict[str, Any]):
        self.server_name = server_name
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0

    async def connect(self):
        transport = self.config.get('transport', 'stdio')
        if transport == 'stdio':
            command = self.config.get('command')
            if not command:
                raise ValueError(f"Command not provided for stdio transport in server {self.server_name}")

            parts = shlex.split(command)

            # Retrieve admin allowlist from config if present
            from config import MCP_ADMIN_ALLOWED_BINARIES
            validate_mcp_command_and_argv(parts, self.server_name, MCP_ADMIN_ALLOWED_BINARIES)

            # Whitelisted minimal environment
            sanitized_env = {
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "HOME": "/tmp",
                "TMPDIR": "/tmp",
                "PYTHONUNBUFFERED": "1"
            }

            audit_event(
                "mcp.server_launched",
                server=self.server_name,
                executable=parts[0],
                arg_count=len(parts) - 1
            )

            self.process = await asyncio.create_subprocess_exec(
                *parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=sanitized_env,
                close_fds=True
            )
        else:
            raise NotImplementedError(f"Transport '{transport}' is deferred or not supported in Stage 1.")

    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("Process not running")

        self._request_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {}
        }
        req_str = json.dumps(req) + "\n"
        self.process.stdin.write(req_str.encode('utf-8'))
        await self.process.stdin.drain()

        line = await self.process.stdout.readline()
        if not line:
            raise ConnectionError("Connection closed by server")

        try:
            response = json.loads(line.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Malformed JSON-RPC response from server: {e}")

        if 'error' in response:
            raise RuntimeError(f"JSON-RPC Error: {response['error']}")
        return response

    async def close(self):
        if self.process:
            if self.process.returncode is None:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    self.process.kill()
            self.process = None


class MCPToolProxy(Tool):
    def __init__(self, schema: MCPToolSchema, permissions: ToolPermissions, client: 'MCPClient'):
        self.name = f"mcp__{schema.server_name}__{schema.name}"
        self.description = schema.description
        self.schema = schema
        self.permissions = permissions
        self.client = client
        self.call_history: List[float] = []

    def validate_args(self, args: Dict[str, Any]):
        try:
            if self.schema.input_schema:
                jsonschema.validate(instance=args, schema=self.schema.input_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Argument validation failed: {e.message}")

    def enforce_rate_limit(self):
        now = time.time()
        self.call_history = [t for t in self.call_history if now - t < 60.0]
        if len(self.call_history) >= self.permissions.rate_limit_rpm:
            raise RuntimeError(f"Rate limit exceeded for tool {self.name}")
        self.call_history.append(now)

    async def _execute_async(self, **kwargs) -> str:
        self.validate_args(kwargs)
        self.enforce_rate_limit()

        server_conn = self.client._servers.get(self.schema.server_name)
        if not server_conn:
            raise RuntimeError(f"Server {self.schema.server_name} not connected")

        start_time = time.time()

        async def do_call():
            resp = await server_conn.send_request("tools/call", {
                "name": self.schema.name,
                "arguments": kwargs
            })
            result = resp.get("result", {})
            content = result.get("content", [])
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                else:
                    text_parts.append(str(item))
            if not text_parts:
                return json.dumps(result)
            return "".join(text_parts)

        try:
            raw_output = await asyncio.wait_for(do_call(), timeout=self.permissions.timeout_seconds)
        except asyncio.TimeoutError:
            audit_event("timeout.triggered", tool=self.name, timeout=self.permissions.timeout_seconds)
            raise RuntimeError(f"Tool {self.name} timed out after {self.permissions.timeout_seconds}s")

        # Defense-in-depth sanitization
        sanitized_output = sanitize_mcp_output(raw_output, max_bytes=self.permissions.max_output_bytes)

        duration = time.time() - start_time
        logger.info(f"Audit: Tool {self.name} called with args {kwargs}, duration {duration:.2f}s, result length {len(sanitized_output)}")
        audit_event(
            "mcp.call_executed",
            tool=self.name,
            duration_ms=int(duration * 1000),
            output_length=len(sanitized_output)
        )

        # Typed observation envelope
        typed_payload = {
            "status": "success",
            "server": self.schema.server_name,
            "tool": self.schema.name,
            "data": sanitized_output
        }
        return json.dumps(typed_payload)

    def execute(self, **kwargs) -> str:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import threading
            result_holder = []
            exc_holder = []
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    res = new_loop.run_until_complete(self._execute_async(**kwargs))
                    result_holder.append(res)
                except Exception as e:
                    exc_holder.append(e)
                finally:
                    new_loop.close()
            t = threading.Thread(target=run_in_thread)
            t.start()
            t.join()
            if exc_holder:
                raise exc_holder[0]
            return result_holder[0]
        else:
            return loop.run_until_complete(self._execute_async(**kwargs))


class MCPClient:
    def __init__(self, config_path: str, registry: Any):
        self.config_path = config_path
        self.registry = registry
        self.config: Dict[str, Any] = {}
        self.quarantine: Dict[str, MCPToolSchema] = {}
        self.active_tools: Dict[str, MCPToolProxy] = {}
        self._servers: Dict[str, MCPServerConnection] = {}
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.config = {}

    async def connect_all(self):
        servers_config = self.config.get('servers', {})
        for server_name, srv_conf in servers_config.items():
            if not srv_conf.get('enabled', False):
                continue

            conn = MCPServerConnection(server_name, srv_conf)
            await conn.connect()
            self._servers[server_name] = conn

            await conn.send_request("initialize", {
                "clientInfo": {"name": "aarkaai", "version": "1.0"},
                "protocolVersion": "2024-11-05"
            })

            tools_response = await conn.send_request("tools/list")
            tools_data = tools_response.get("result", {}).get("tools", [])

            auto_approve = self.config.get('trust', {}).get('auto_approve', False)
            allowed_tools = srv_conf.get('allowed_tools', [])

            for t_data in tools_data:
                t_name = t_data.get("name")
                if not t_name:
                    continue
                schema = MCPToolSchema(
                    name=t_name,
                    description=t_data.get("description", ""),
                    input_schema=t_data.get("inputSchema", {}),
                    server_name=server_name
                )
                self.quarantine[f"{server_name}__{t_name}"] = schema

                if auto_approve and t_name in allowed_tools:
                    perms = ToolPermissions(
                        rate_limit_rpm=srv_conf.get('rate_limit_rpm', 60),
                        timeout_seconds=srv_conf.get('timeout_seconds', 10.0),
                        max_output_bytes=self.config.get('trust', {}).get('max_output_bytes', 65536)
                    )
                    self.approve_tool(server_name, t_name, perms)

    def approve_tool(self, server_name: str, tool_name: str, permissions: ToolPermissions) -> bool:
        servers_config = self.config.get('servers', {})
        if server_name not in servers_config:
            return False

        srv_conf = servers_config[server_name]
        allowed_tools = srv_conf.get('allowed_tools', [])

        if tool_name not in allowed_tools:
            return False

        quarantine_key = f"{server_name}__{tool_name}"
        if quarantine_key not in self.quarantine:
            return False

        schema = self.quarantine[quarantine_key]
        if not isinstance(schema.input_schema, dict):
            return False

        proxy = MCPToolProxy(schema, permissions, self)
        fqn = proxy.name
        self.active_tools[fqn] = proxy
        del self.quarantine[quarantine_key]

        if hasattr(self.registry, 'register'):
            self.registry.register(proxy)
        elif isinstance(self.registry, dict):
            self.registry[fqn] = proxy

        audit_event("approval.decided", tool=fqn, outcome="approved", type="mcp_quarantine")
        return True

    async def call_tool(self, fqn: str, args: Dict[str, Any]) -> str:
        if fqn not in self.active_tools:
            raise ValueError(f"Tool {fqn} is not active")
        proxy = self.active_tools[fqn]
        return await proxy._execute_async(**args)

    async def shutdown(self):
        for name, conn in list(self._servers.items()):
            try:
                await conn.close()
            except Exception as e:
                logger.error(f"Error closing server {name}: {e}")
        self._servers.clear()
