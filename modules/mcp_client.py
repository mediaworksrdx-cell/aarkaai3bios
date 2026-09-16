import asyncio
import json
import yaml
import time
import logging
import dataclasses
from typing import Any, Dict, List, Optional
import jsonschema

# Assuming modules.tools.base.Tool exists as described
try:
    from modules.tools.base import Tool
except ImportError:
    class Tool:
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description
        def execute(self, **kwargs) -> str:
            raise NotImplementedError

logger = logging.getLogger(__name__)

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
            
            import shlex
            parts = shlex.split(command)
            self.process = await asyncio.create_subprocess_exec(
                *parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            raise NotImplementedError(f"Transport {transport} not supported")

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

        # Simple line-by-line reading for stdio json-rpc
        line = await self.process.stdout.readline()
        if not line:
            raise ConnectionError("Connection closed by server")
        
        response = json.loads(line.decode('utf-8'))
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
        # Tool base class uses class-level attributes, not __init__ params
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
        # Sliding window of 60 seconds for RPM
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
        
        # Async execution with timeout
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
            raise RuntimeError(f"Tool {self.name} timed out after {self.permissions.timeout_seconds}s")
        except Exception as e:
            raise e
        
        # Output truncation
        output_bytes = raw_output.encode('utf-8')
        if len(output_bytes) > self.permissions.max_output_bytes:
            output_bytes = output_bytes[:self.permissions.max_output_bytes]
            raw_output = output_bytes.decode('utf-8', errors='ignore') + "... (truncated)"
        
        duration = time.time() - start_time
        logger.info(
            f"Audit: Tool '{self.name}' called with args {kwargs}. "
            f"Duration: {duration:.3f}s. Result length: {len(raw_output)} chars."
        )

        return raw_output

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
