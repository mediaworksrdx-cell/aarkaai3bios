import ast
import dataclasses
import json
import logging
import subprocess
import os
import textwrap

logger = logging.getLogger(__name__)

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
    def __init__(self, tool_registry, workspace_dir: str, timeout: float, max_tool_calls: int, max_output_bytes: int):
        self.registry = tool_registry
        self.workspace_dir = workspace_dir
        self.timeout = timeout
        self.max_tool_calls = max_tool_calls
        self.max_output_bytes = max_output_bytes
        self.call_count = 0

    def build_tool_namespace(self, allowed_tools: list[str]) -> dict:
        namespace = {}
        for name in allowed_tools:
            def make_proxy(tool_name):
                def proxy(**kwargs):
                    self.call_count += 1
                    if self.call_count > self.max_tool_calls:
                        raise RuntimeError(f"Max tool calls ({self.max_tool_calls}) exceeded")
                    return self.registry.execute_tool(tool_name, kwargs)
                return proxy
            namespace[name] = make_proxy(name)
        return namespace

    def execute_code_block(self, code: str, namespace: dict, user_id: str, session_id: str) -> CodeModeResult:
        is_valid, error = self.validate_code(code)
        if not is_valid:
            return CodeModeResult(success=False, output="", tool_calls=[], error=error)

        allowed_tools = list(namespace.keys())
        indented_code = textwrap.indent(code, '    ')

        runner_code = SUBPROCESS_RUNNER_TEMPLATE.format(
            allowed_tools_json=json.dumps(allowed_tools),
            user_code=indented_code
        )

        script_path = os.path.join(self.workspace_dir, "code_mode_runner.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(runner_code)

        tool_calls_audit = []
        final_output = []

        try:
            proc = subprocess.Popen(
                ["python", script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.workspace_dir
            )

            import time
            import threading

            start_time = time.time()

            # Use a thread to read stdout line-by-line (Windows-compatible)
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
                    proc.kill()
                    return CodeModeResult(
                        success=False, output="".join(final_output),
                        tool_calls=tool_calls_audit, error="Execution timed out"
                    )

                # Process any new lines
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

            # Truncate output if too large
            output = "".join(final_output)
            if len(output) > self.max_output_bytes:
                output = output[:self.max_output_bytes] + "\n...[output truncated]"

            return CodeModeResult(success=True, output=output, tool_calls=tool_calls_audit)
        finally:
            if os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except Exception:
                    pass

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
