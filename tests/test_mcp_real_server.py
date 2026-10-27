"""
Real Local Stdio MCP Server Integration Test Suite.
Verifies real subprocess lifecycle, JSON-RPC 2.0 handshake, tool discovery,
schema validation, tool invocation, and process cleanup.
Separated strictly from unit tests using mocks.
"""

import asyncio
import os
import sys
import yaml
import pytest

from modules.mcp_client import MCPServerConnection, MCPClient


@pytest.fixture
def real_mcp_server_config(tmp_path):
    helper_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "helpers", "mock_mcp_server.py")
    )
    python_exe = sys.executable

    config = {
        "trust": {
            "require_authentication": False,
            "auto_approve": True,
            "max_output_bytes": 65536,
            "default_timeout_seconds": 5.0
        },
        "servers": {
            "real_test_server": {
                "enabled": True,
                "transport": "stdio",
                "command": f'"{python_exe}" "{helper_script}"',
                "allowed_tools": ["echo_tool", "add_tool"],
                "rate_limit_rpm": 120,
                "timeout_seconds": 5.0
            }
        }
    }
    p = tmp_path / "mcp_real_config.yaml"
    p.write_text(yaml.dump(config), encoding="utf-8")
    return str(p), helper_script


def test_real_mcp_connection_and_handshake(real_mcp_server_config):
    """Verifies actual process launch and JSON-RPC initialize handshake."""
    _, helper_script = real_mcp_server_config
    server_cfg = {
        "transport": "stdio",
        "command": f'"{sys.executable}" "{helper_script}"'
    }

    async def _run():
        conn = MCPServerConnection("real_test_server", server_cfg)
        await conn.connect()
        try:
            assert conn.process is not None
            assert conn.process.returncode is None

            # Send initialize handshake
            resp = await conn.send_request("initialize", {"protocolVersion": "2024-11-05"})
            assert resp.get("jsonrpc") == "2.0"
            result = resp.get("result", {})
            assert "capabilities" in result
            assert result.get("serverInfo", {}).get("name") == "aarkaa-real-test-server"
        finally:
            await conn.close()
            assert conn.process is None or conn.process.returncode is not None

    asyncio.run(_run())


def test_real_mcp_tool_discovery_and_execution(real_mcp_server_config):
    """Verifies tools/list discovery and tools/call execution against real stdio process."""
    _, helper_script = real_mcp_server_config
    server_cfg = {
        "transport": "stdio",
        "command": f'"{sys.executable}" "{helper_script}"'
    }

    async def _run():
        conn = MCPServerConnection("real_test_server", server_cfg)
        await conn.connect()
        try:
            # 1. Discover tools
            list_resp = await conn.send_request("tools/list")
            tools = list_resp.get("result", {}).get("tools", [])
            tool_names = [t["name"] for t in tools]
            assert "echo_tool" in tool_names
            assert "add_tool" in tool_names

            # 2. Call echo_tool
            call_resp = await conn.send_request("tools/call", {
                "name": "echo_tool",
                "arguments": {"message": "Hello MCP Real Server"}
            })
            content = call_resp.get("result", {}).get("content", [])
            assert len(content) == 1
            assert content[0]["text"] == "ECHO: Hello MCP Real Server"

            # 3. Call add_tool
            add_resp = await conn.send_request("tools/call", {
                "name": "add_tool",
                "arguments": {"a": 40, "b": 2}
            })
            add_content = add_resp.get("result", {}).get("content", [])
            assert len(add_content) == 1
            assert add_content[0]["text"] == "SUM: 42"
        finally:
            await conn.close()

    asyncio.run(_run())


def test_real_mcp_client_quarantine_and_registration(real_mcp_server_config):
    """Verifies MCPClient auto-registers and proxies approved tools from real server."""
    config_path, _ = real_mcp_server_config
    registry = {}

    async def _run():
        client = MCPClient(config_path, registry)
        try:
            await client.connect_all()
            assert len(client.active_tools) >= 2
            assert "mcp__real_test_server__echo_tool" in registry
            assert "mcp__real_test_server__add_tool" in registry

            # Execute registered proxy tool through client.call_tool
            result = await client.call_tool("mcp__real_test_server__echo_tool", {"message": "Verified Integration"})
            assert "ECHO: Verified Integration" in result
        finally:
            await client.shutdown()

    asyncio.run(_run())


def test_real_mcp_tool_schema_validation_failure(real_mcp_server_config):
    """Verifies proxy tool rejects invalid arguments before transmission."""
    config_path, _ = real_mcp_server_config
    registry = {}

    async def _run():
        client = MCPClient(config_path, registry)
        try:
            await client.connect_all()

            # Missing required parameter 'b'
            with pytest.raises(ValueError, match="Argument validation failed"):
                await client.call_tool("mcp__real_test_server__add_tool", {"a": 10})

            # Invalid type: string instead of number
            with pytest.raises(ValueError, match="Argument validation failed"):
                await client.call_tool("mcp__real_test_server__add_tool", {"a": 10, "b": "not-a-number"})
        finally:
            await client.shutdown()

    asyncio.run(_run())
