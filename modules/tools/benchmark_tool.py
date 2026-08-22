import subprocess
import sys
import time
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path
from config import BASH_TIMEOUT, SAFE_WORK_DIR

class BenchmarkTool(Tool):
    name = "BenchmarkTool"
    description = "Trace speed performance statistics and execution bottlenecks on target code blocks."
    risk_level = "LOW"
    latency_weight = 1.6
    cost_weight = 0.3
    base_confidence = 0.99

    permissions = ["read", "execute"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 3000

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)

            # SEC-C1 FIX: Execute in an isolated subprocess instead of exec()
            # This prevents arbitrary code from accessing the parent process's
            # memory, globals, imports, or environment.
            start_t = time.perf_counter()
            result = subprocess.run(
                [sys.executable, str(resolved)],
                capture_output=True,
                text=True,
                timeout=BASH_TIMEOUT,
                cwd=str(SAFE_WORK_DIR),
            )
            elapsed = time.perf_counter() - start_t

            output = f"Benchmark completed.\nTotal Execution Time: {elapsed:.4f} seconds\n"
            if result.stdout:
                output += f"\n[stdout]\n{result.stdout[:2000]}\n"
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr[:1000]}\n"
            output += f"Exit code: {result.returncode}"
            return output
        except subprocess.TimeoutExpired:
            return f"Error: Benchmark timed out after {BASH_TIMEOUT} seconds."
        except Exception as e:
            return f"Performance benchmark run error: {e}"
