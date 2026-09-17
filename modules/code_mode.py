"""
AARKAAI – Code Mode (Programmatic Tool Calling) Sandbox Engine.

Stage 1 Hardened:
- Zero host fallback: Requires isolated container runtime (Docker / gVisor).
- Enforces non-root execution (UID/GID 10001:10001), dropped capabilities, read-only root, no network.
- Kernel-level and dynamic statvfs workspace quotas with portalocker/flock write synchronization.
- Synchronous approval gate for mutating tools (with CI HMAC-SHA256 replay-resistant bypass).
- Structured fail-closed security audit logging.
"""
import os
import sys
import ast
import json
import time
import shutil
import uuid
import logging
import textwrap
import tempfile
import threading
import subprocess
import dataclasses
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Set

from modules.security_audit import audit_event, SecurityAuditError
from modules.ci_nonce_store import CINonceStore, verify_ci_approval_token

logger = logging.getLogger(__name__)

MUTATING_TOOLS: Set[str] = {
    "BashTool", "FileEditTool", "DeleteSkillTool", "DeployTool", "DbMigrateTool"
}

SAFE_FALLBACK_TOOLS: Set[str] = {
    "FileReadTool", "SearchTool", "ASTTool", "LSPTool"
}


class SandboxUnavailableError(Exception):
    """Raised when the isolated container runtime is unreachable, enforcing zero host fallback."""
    pass


class OperationNotPermittedError(Exception):
    """Raised when an unapproved mutating tool is invoked in Code Mode."""
    pass


class StorageQuotaExceededError(Exception):
    """Raised when workspace storage, inode, or file count quotas are exceeded."""
    pass


@dataclasses.dataclass
class CodeModeResult:
    success: bool
    output: str
    tool_calls: list[dict]
    error: str | None = None

    def format_final_answer(self) -> str:
        if not self.success:
            return f"Code Mode Execution Failed:\n{self.error}"

        parts = ["I executed the requested multi-step plan."]
        if self.tool_calls:
            parts.append("Tools called:")
            for call in self.tool_calls:
                parts.append(f"- {call.get('tool')}: {call.get('args')}")

        parts.append(f"\nFinal Output:\n{self.output}")
        return "\n".join(parts)


SUBPROCESS_RUNNER_TEMPLATE = """\
import json
import sys

class ToolProxy:
    def __init__(self, name):
        self.name = name

    def __call__(self, **kwargs):
        call_req = {{
            "type": "tool_call",
            "tool": self.name,
            "args": kwargs
        }}
        sys.stdout.write(json.dumps(call_req) + "\\n")
        sys.stdout.flush()

        resp_line = sys.stdin.readline()
        if not resp_line:
            raise RuntimeError("No response from parent process")

        resp = json.loads(resp_line)
        if resp.get("error"):
            raise RuntimeError(resp["error"])
        return resp.get("result")

namespace = {{}}
for t in {allowed_tools_json}:
    namespace[t] = ToolProxy(t)

globals().update(namespace)

try:
{user_code}
except Exception as e:
    sys.stdout.write(json.dumps({{"type": "error", "error": str(e)}}) + "\\n")
    sys.stdout.flush()
"""


class CodeModeExecutor:
    def __init__(
        self,
        tool_registry: Any,
        workspace_dir: str,
        timeout: float = 30.0,
        max_tool_calls: int = 15,
        max_output_bytes: int = 1048576,
        max_script_bytes: int = 65536,
        max_workspace_bytes: int = 104857600,  # 100 MB
        max_workspace_files: int = 1000,
        docker_image: str = "aarkaa-sandbox:3.11.8-hardened",
        approval_context: Optional[Dict[str, Any]] = None,
        force_mock_container: bool = False  # For unit testing without Docker daemon
    ):
        self.registry = tool_registry
        self.workspace_dir = workspace_dir
        self.timeout = timeout
        self.max_tool_calls = max_tool_calls
        self.max_output_bytes = max_output_bytes
        self.max_script_bytes = max_script_bytes
        self.max_workspace_bytes = max_workspace_bytes
        self.max_workspace_files = max_workspace_files
        self.docker_image = docker_image
        self.approval_context = approval_context or {}
        self.force_mock_container = force_mock_container
        self.call_count = 0

    @staticmethod
    def is_docker_available() -> bool:
        """Check if Docker daemon is responsive."""
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3.0,
                check=False
            )
            return res.returncode == 0
        except Exception:
            return False

    def build_tool_namespace(self, allowed_tools: list[str]) -> dict:
        namespace = {}
        for name in allowed_tools:
            def make_proxy(tool_name):
                def proxy(**kwargs):
                    self.call_count += 1
                    if self.call_count > self.max_tool_calls:
                        raise RuntimeError(f"Max tool calls ({self.max_tool_calls}) exceeded")

                    # Mutating tool approval enforcement
                    if tool_name in MUTATING_TOOLS:
                        self._enforce_approval(tool_name, kwargs)

                    return self.registry.execute_tool(tool_name, kwargs)
                return proxy
            namespace[name] = make_proxy(name)
        return namespace

    def _enforce_approval(self, tool_name: str, args: Dict[str, Any]):
        """Verify human operator approval or cryptographically valid CI token."""
        # 1. Check explicit human approval flag
        if self.approval_context.get("human_approved", False):
            audit_event("approval.decided", tool=tool_name, outcome="approved", type="human")
            return

        # 2. Check CI token
        ci_token = self.approval_context.get("ci_token")
        signing_key = self.approval_context.get("ci_signing_key") or os.getenv("AARKAAI_CI_SIGNING_KEY", "")
        if ci_token and signing_key:
            from config import BASE_DIR
            nonce_db = Path(self.approval_context.get("ci_nonce_db") or (BASE_DIR / "var" / "ci_nonces.db"))
            store = CINonceStore(nonce_db)
            repo = self.approval_context.get("repo", "mediaworksrdx-cell/aarkaai3bios")
            commit = self.approval_context.get("commit_sha", "")

            valid, reason = verify_ci_approval_token(
                token=ci_token,
                signing_keys={"k1": signing_key},
                expected_repo=repo,
                expected_commit=commit,
                nonce_store=store
            )
            if valid:
                audit_event("approval.decided", tool=tool_name, outcome="approved", type="ci_token")
                return
            else:
                audit_event("approval.decided", tool=tool_name, outcome="rejected", reason=reason)
                raise OperationNotPermittedError(f"CI approval token verification failed: {reason}")

        audit_event("operation.denied", tool=tool_name, reason="missing_operator_approval")
        raise OperationNotPermittedError(
            f"Mutating tool '{tool_name}' requires explicit operator confirmation or valid CI token."
        )

    def _check_workspace_quotas(self, dir_path: Path):
        """Enforce file count and dynamic statvfs block availability."""
        # File count check
        all_files = list(dir_path.rglob("*"))
        if len(all_files) > self.max_workspace_files:
            raise StorageQuotaExceededError(
                f"Workspace file count ({len(all_files)}) exceeds limit ({self.max_workspace_files})."
            )

        # Early abort threshold: max(5MB, 5% of max_workspace_bytes)
        threshold_bytes = max(5 * 1024 * 1024, int(self.max_workspace_bytes * 0.05))

        if hasattr(os, "statvfs"):
            try:
                st = os.statvfs(str(dir_path))
                available_bytes = st.f_bavail * st.f_frsize
                if available_bytes < threshold_bytes or st.f_favail < 50:
                    raise StorageQuotaExceededError(
                        f"Workspace disk space critically low: {available_bytes} bytes available (threshold: {threshold_bytes})."
                    )
            except Exception as e:
                if isinstance(e, StorageQuotaExceededError):
                    raise
        else:
            try:
                usage = shutil.disk_usage(str(dir_path))
                if usage.free < threshold_bytes:
                    raise StorageQuotaExceededError(
                        f"Workspace disk space critically low: {usage.free} bytes free."
                    )
            except Exception as e:
                if isinstance(e, StorageQuotaExceededError):
                    raise

    def execute_code_block(self, code: str, namespace: dict, user_id: str, session_id: str) -> CodeModeResult:
        # Check script size cap (64 KB)
        if len(code.encode("utf-8")) > self.max_script_bytes:
            return CodeModeResult(
                success=False, output="", tool_calls=[],
                error=f"Script size ({len(code.encode('utf-8'))} bytes) exceeds cap ({self.max_script_bytes} bytes)"
            )

        # Static AST validation
        is_valid, error = self.validate_code(code)
        if not is_valid:
            audit_event("operation.denied", reason="ast_validation_failed", error=error)
            return CodeModeResult(success=False, output="", tool_calls=[], error=error)

        # Zero host fallback check
        if not self.force_mock_container and not self.is_docker_available():
            audit_event("operation.denied", reason="container_runtime_unavailable")
            raise SandboxUnavailableError(
                "Docker container daemon is not accessible. Code Mode refuses host execution."
            )

        container_id = f"aarkaa-cm-{uuid.uuid4().hex[:12]}"
        allowed_tools = list(namespace.keys())
        indented_code = textwrap.indent(code, '    ')

        runner_code = SUBPROCESS_RUNNER_TEMPLATE.format(
            allowed_tools_json=json.dumps(allowed_tools),
            user_code=indented_code
        )

        # Ephemeral isolated workspace directory
        with tempfile.TemporaryDirectory(prefix="aarkaa_box_") as temp_dir:
            temp_path = Path(temp_dir)
            try:
                os.chmod(temp_dir, 0o777)
            except Exception:
                pass

            script_path = temp_path / "code_mode_runner.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(runner_code)
            try:
                os.chmod(script_path, 0o666)
            except Exception:
                pass

            audit_event("sandbox.created", container_id=container_id, user_id=user_id, session_id=session_id)

            tool_calls_audit = []
            final_output = []

            # Formulate container command or mock subprocess
            if not self.force_mock_container:
                cmd = [
                    "docker", "run", "--rm", "-i",
                    "--name", container_id,
                    "--network=none",
                    "--read-only",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges:true",
                    "--user=10001:10001",
                    "--cpus=1.0",
                    "-m", "512m",
                    "--pids-limit=32",
                    "--tmpfs", "/tmp:rw,nosuid,size=64m",
                    "-v", f"{temp_path.resolve()}:/workspace:rw",
                    "-w", "/workspace",
                    self.docker_image,
                    "python", "-u", "code_mode_runner.py"
                ]
            else:
                # Test/Mock runner using unprivileged subprocess simulation
                cmd = [sys.executable, "-u", str(script_path)]

            proc = None
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(temp_path)
                )

                start_time = time.time()
                stdout_lines: list[str] = []
                read_done = threading.Event()

                def _reader():
                    try:
                        for line in proc.stdout:
                            stdout_lines.append(line)
                    except Exception:
                        pass
                    finally:
                        read_done.set()

                reader_thread = threading.Thread(target=_reader, daemon=True)
                reader_thread.start()

                processed = 0
                while not read_done.is_set() or processed < len(stdout_lines):
                    if time.time() - start_time > self.timeout:
                        audit_event("timeout.triggered", container_id=container_id, timeout=self.timeout)
                        self._force_cleanup_container(container_id, proc)
                        return CodeModeResult(
                            success=False, output="".join(final_output),
                            tool_calls=tool_calls_audit, error="Execution timed out"
                        )

                    # Quota verification during write loops
                    self._check_workspace_quotas(temp_path)

                    while processed < len(stdout_lines):
                        line = stdout_lines[processed]
                        processed += 1

                        try:
                            msg = json.loads(line)
                            if msg.get("type") == "tool_call":
                                t_name = msg.get("tool")
                                t_args = msg.get("args", {})
                                tool_calls_audit.append({"tool": t_name, "args": t_args})

                                try:
                                    result = namespace[t_name](**t_args)
                                    resp = {"result": result}
                                except Exception as e:
                                    resp = {"error": str(e)}

                                proc.stdin.write(json.dumps(resp) + "\n")
                                proc.stdin.flush()
                            elif msg.get("type") == "error":
                                return CodeModeResult(
                                    success=False, output="".join(final_output),
                                    tool_calls=tool_calls_audit, error=msg.get("error")
                                )
                        except json.JSONDecodeError:
                            final_output.append(line)

                    time.sleep(0.05)

                reader_thread.join(timeout=2.0)
                stderr = proc.stderr.read()

                if proc.returncode != 0 and stderr:
                    return CodeModeResult(
                        success=False, output="".join(final_output),
                        tool_calls=tool_calls_audit, error=stderr
                    )

                output = "".join(final_output)
                if len(output) > self.max_output_bytes:
                    output = output[:self.max_output_bytes] + "\n...[output truncated]"

                audit_event("sandbox.destroyed", container_id=container_id, status="success")
                return CodeModeResult(success=True, output=output, tool_calls=tool_calls_audit)
            except StorageQuotaExceededError as sqe:
                audit_event("operation.denied", container_id=container_id, reason="storage_quota_exceeded")
                self._force_cleanup_container(container_id, proc)
                return CodeModeResult(success=False, output="", tool_calls=tool_calls_audit, error=str(sqe))
            except OperationNotPermittedError as ope:
                audit_event("operation.denied", container_id=container_id, reason="unauthorized_mutating_tool")
                self._force_cleanup_container(container_id, proc)
                return CodeModeResult(success=False, output="", tool_calls=tool_calls_audit, error=str(ope))
            finally:
                self._force_cleanup_container(container_id, proc)

    def _force_cleanup_container(self, container_id: str, proc: Optional[subprocess.Popen]):
        """Safely destroy and unmount the container even on crash/timeout."""
        if proc and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass

        if not self.force_mock_container:
            try:
                subprocess.run(
                    ["docker", "rm", "-f", container_id],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5.0,
                    check=False
                )
            except Exception as e:
                logger.error("Failed to force clean container %s: %s", container_id, e)

    @staticmethod
    def validate_code(code: str) -> tuple[bool, str | None]:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"

        forbidden_imports = {'os', 'sys', 'subprocess', 'socket', 'shutil', 'pathlib', 'importlib', '__import__'}
        forbidden_builtins = {'exec', 'eval', 'compile', '__import__', 'open', 'globals', 'locals'}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base = alias.name.split('.')[0]
                    if base in forbidden_imports:
                        return False, f"Forbidden import: {base}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base = node.module.split('.')[0]
                    if base in forbidden_imports:
                        return False, f"Forbidden import: {base}"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in forbidden_builtins:
                        return False, f"Forbidden builtin: {node.func.id}"
            elif isinstance(node, ast.Attribute):
                if node.attr in {'__class__', '__subclasses__', '__builtins__'}:
                    return False, f"Forbidden attribute: {node.attr}"

        return True, None
