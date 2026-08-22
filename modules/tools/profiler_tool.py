import subprocess
import sys
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path
from config import BASH_TIMEOUT, SAFE_WORK_DIR


class ProfilerTool(Tool):
    name = "ProfilerTool"
    description = (
        "Run python target files under cProfile in an isolated subprocess to trace "
        "execution hotspots, function call counts, and execution bottlenecks."
    )
    risk_level = "LOW"
    latency_weight = 1.6
    cost_weight = 0.3
    base_confidence = 0.99

    permissions = ["read", "execute"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 2500

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)

            # SEC-C1 FIX: Run cProfile in an isolated subprocess instead of exec()
            # Uses 'python -m cProfile -s cumulative <script>' which outputs the
            # profiling table to stdout without needing exec() in the parent process.
            result = subprocess.run(
                [sys.executable, "-m", "cProfile", "-s", "cumulative", str(resolved)],
                capture_output=True,
                text=True,
                timeout=BASH_TIMEOUT,
                cwd=str(SAFE_WORK_DIR),
            )

            output = ""
            if result.stdout:
                # cProfile output goes to stdout; truncate to top 30 entries
                lines = result.stdout.strip().split("\n")
                # Find the start of the profile stats table
                stats_start = 0
                for i, line in enumerate(lines):
                    if "ncalls" in line and "tottime" in line:
                        stats_start = i
                        break
                # Keep header + top 30 function entries
                profile_lines = lines[stats_start:stats_start + 32]
                output = "Profile trace (top 30 hotspots):\n" + "\n".join(profile_lines)
            if result.stderr:
                output += f"\n\n[stderr]\n{result.stderr[:1000]}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"

            return output if output else "Profiling completed with no output."

        except subprocess.TimeoutExpired:
            return f"Error: Profiler execution timed out after {BASH_TIMEOUT} seconds."
        except Exception as e:
            return f"Execution profiling error: {e}"
