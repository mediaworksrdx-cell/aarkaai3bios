import os
import subprocess
import tempfile
from typing import Any, Dict
from modules.tools.base import Tool
import config

class FinanceCodeTool(Tool):
    name = "FinanceCodeTool"
    description = "Execute Python code for approved financial calculations and analysis. Actions: execute"
    risk_level = "HIGH"
    latency_weight = 2.5
    cost_weight = 1.0
    base_confidence = 0.85
    permissions = ["execute"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 5000

    BLOCKED_PATTERNS = [
        "import os", "import sys", "import subprocess", "import socket",
        "import requests", "import urllib", "open(", "exec(", "eval(",
        "__import__", "compile("
    ]

    PRE_IMPORTS = """import pandas as pd
import numpy as np
import math
import statistics
import datetime
import json
"""

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        try:
            if action == "execute":
                return self._handle_execute(params)
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"

    def _handle_execute(self, params: Dict[str, Any]) -> str:
        code = params.get("code")
        if not code:
            return "Error: 'code' parameter is required for execute action."
        
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in code:
                return f"Error: Code contains blocked pattern: {pattern}"
                
        full_code = self.PRE_IMPORTS + "\n" + code
        
        try:
            safe_dir = getattr(config, "SAFE_WORK_DIR", tempfile.gettempdir())
            if not os.path.exists(safe_dir):
                os.makedirs(safe_dir, exist_ok=True)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=safe_dir, delete=False) as f:
                f.write(full_code)
                temp_path = f.name
                
            timeout = getattr(config, "BASH_TIMEOUT", 30)
            
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out."
        except Exception as e:
            return f"Error executing code: {e}"
        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
                
        return output
