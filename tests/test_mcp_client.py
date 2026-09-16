"""
Tests for MCP Client (Phase 5).
Validates quarantine-first architecture, tool approval, rate limiting,
timeout enforcement, output truncation, and audit logging.

All async operations are wrapped in asyncio.run() for compatibility
with pytest environments that do not have pytest-asyncio installed.
"""
import asyncio
import json
import yaml
import time
import logging
import pytest
from unittest.mock import Mock, patch, AsyncMock
from modules.mcp_client import (
    MCPClient, MCPToolProxy, MCPToolSchema, ToolPermissions, MCPServerConnection
)


@pytest.fixture
def mock_registry():
    return {}


@pytest.fixture
def config_file(tmp_path):
    config = {
        "trust": {
            "require_authentication": True,
            "auto_approve": False,
            "max_output_bytes": 100,
            "default_timeout_seconds": 1.0
        },
        "servers": {
            "test_server": {
                "enabled": True,
                "transport": "stdio",
                "command": "dummy",
                "allowed_tools": ["test_tool"],
                "rate_limit_rpm": 60,
                "timeout_seconds": 1.0
            },
            "disabled_server": {
                "enabled": False,
                "transport": "stdio",
                "command": "dummy",
                "allowed_tools": ["ignored_tool"]
            }
        }
    }
    p = tmp_path / "mcp_config.yaml"
    p.write_text(yaml.dump(config))
    return str(p)


def _make_mock_conn():
    """Create a mock MCPServerConnection with standard test responses."""
    instance = AsyncMock()

    async def mock_send_request(method, params=None):
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": 1, "result": {}}
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": [
                        {
                            "name": "test_tool",
                            "description": "A test tool",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"arg1": {"type": "string"}},
                                "required": ["arg1"]
                            }
                        },
                        {
                            "name": "unapproved_tool",
                            "description": "Should not be approved",
                            "inputSchema": {"type": "object"}
                        }
                    ]
                }
            }
        elif method == "tools/call":
            if params and params.get("name") == "test_tool":
                return {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {
                        "content": [{"type": "text", "text": "test output"}]
                    }
                }
        return {"jsonrpc": "2.0", "id": 99, "result": {}}

    instance.send_request = mock_send_request
    return instance


def test_quarantine_on_discovery(config_file, mock_registry):
    """Discovered tools enter quarantine, not active registry."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        mock_conn.return_value = _make_mock_conn()
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())

    assert "test_server__test_tool" in client.quarantine
    assert "test_server__unapproved_tool" in client.quarantine
    assert not client.active_tools


def test_approve_moves_to_registry(config_file, mock_registry):
    """Approved tool appears in active registry with correct FQN."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        mock_conn.return_value = _make_mock_conn()
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())

    perms = ToolPermissions()
    success = client.approve_tool("test_server", "test_tool", perms)

    assert success is True
    assert "test_server__test_tool" not in client.quarantine
    assert "mcp__test_server__test_tool" in client.active_tools
    assert "mcp__test_server__test_tool" in mock_registry


def test_reject_tool_not_in_allowlist(config_file, mock_registry):
    """Tool not in allowlist is rejected."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        mock_conn.return_value = _make_mock_conn()
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())

    perms = ToolPermissions()
    success = client.approve_tool("test_server", "unapproved_tool", perms)

    assert success is False
    assert "test_server__unapproved_tool" in client.quarantine
    assert "mcp__test_server__unapproved_tool" not in client.active_tools


def test_rate_limiting(config_file, mock_registry):
    """Exceeding rate limit raises error."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        mock_conn.return_value = _make_mock_conn()
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())
        client.approve_tool("test_server", "test_tool", ToolPermissions(rate_limit_rpm=2))

        async def _run():
            await client.call_tool("mcp__test_server__test_tool", {"arg1": "a"})
            await client.call_tool("mcp__test_server__test_tool", {"arg1": "b"})
            with pytest.raises(RuntimeError, match="Rate limit exceeded"):
                await client.call_tool("mcp__test_server__test_tool", {"arg1": "c"})

        asyncio.run(_run())


def test_timeout_enforcement(config_file, mock_registry):
    """Slow tool call is cancelled."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        instance = AsyncMock()

        async def slow_send_request(method, params=None):
            if method == "tools/list":
                return {"result": {"tools": [{"name": "test_tool", "inputSchema": {}}]}}
            if method == "tools/call":
                await asyncio.sleep(5.0)
                return {"result": {"content": [{"type": "text", "text": "done"}]}}
            return {}

        instance.send_request = slow_send_request
        mock_conn.return_value = instance

        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())
        client.approve_tool("test_server", "test_tool", ToolPermissions(timeout_seconds=0.1))

        async def _run():
            with pytest.raises(RuntimeError, match="timed out"):
                await client.call_tool("mcp__test_server__test_tool", {})

        asyncio.run(_run())


def test_output_truncation(config_file, mock_registry):
    """Large output is truncated to max_output_bytes."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        instance = AsyncMock()
        long_output = "X" * 200

        async def mock_send_request(method, params=None):
            if method == "tools/list":
                return {"result": {"tools": [{"name": "test_tool", "inputSchema": {}}]}}
            if method == "tools/call":
                return {"result": {"content": [{"type": "text", "text": long_output}]}}
            return {}

        instance.send_request = mock_send_request
        mock_conn.return_value = instance

        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())
        client.approve_tool("test_server", "test_tool", ToolPermissions(max_output_bytes=10))

        async def _run():
            result = await client.call_tool("mcp__test_server__test_tool", {})
            assert "truncated" in result
            assert len(result) < 200

        asyncio.run(_run())


def test_argument_validation(config_file, mock_registry):
    """Invalid args rejected against schema."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        mock_conn.return_value = _make_mock_conn()
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())
        client.approve_tool("test_server", "test_tool", ToolPermissions())

        async def _run():
            with pytest.raises(ValueError, match="Argument validation failed"):
                await client.call_tool("mcp__test_server__test_tool", {"arg1": 123})

        asyncio.run(_run())


def test_shutdown_terminates_processes(config_file, mock_registry):
    """Shutdown kills server processes."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        instance = _make_mock_conn()
        mock_conn.return_value = instance
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())

        assert "test_server" in client._servers
        asyncio.run(client.shutdown())
        assert len(client._servers) == 0


def test_disabled_server_not_connected(config_file, mock_registry):
    """Disabled servers are skipped during connect_all."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        mock_conn.return_value = _make_mock_conn()
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())

    assert "test_server" in client._servers
    assert "disabled_server" not in client._servers


def test_audit_logging(config_file, mock_registry, caplog):
    """Tool calls are logged."""
    with patch('modules.mcp_client.MCPServerConnection') as mock_conn:
        mock_conn.return_value = _make_mock_conn()
        client = MCPClient(config_file, mock_registry)
        asyncio.run(client.connect_all())
        client.approve_tool("test_server", "test_tool", ToolPermissions())

        with caplog.at_level(logging.INFO, logger="modules.mcp_client"):
            asyncio.run(client.call_tool("mcp__test_server__test_tool", {"arg1": "val"}))

    assert any("Audit" in rec.message and "mcp__test_server__test_tool" in rec.message
               for rec in caplog.records)
