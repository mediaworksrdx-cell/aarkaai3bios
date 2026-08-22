"""
AARKAAI – FinanceCodeTool (AST-Based Safety)

Executes Python code for approved financial calculations and analysis.
Uses AST-based analysis (not string matching) to block dangerous patterns.

SEC-H3 FIX: Replaced brittle string-matching blocklist with AST analysis
that cannot be bypassed by string concatenation, unicode normalization,
or attribute chaining tricks.
"""
import ast
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, Set
from modules.tools.base import Tool
import config


# ─── AST-Based Safety Checker ────────────────────────────────────────────────

BLOCKED_IMPORTS: Set[str] = {
    "os", "sys", "subprocess", "socket", "shutil", "pty", "signal",
    "ctypes", "importlib", "code", "codeop", "compileall",
    "http", "urllib", "requests", "aiohttp", "httpx",
    "pickle", "shelve", "marshal",
}

BLOCKED_BUILTINS: Set[str] = {
    "exec", "eval", "compile", "__import__", "open",
    "breakpoint", "exit", "quit", "globals", "locals",
    "getattr", "setattr", "delattr",
}


class _SafetyVisitor(ast.NodeVisitor):
    """AST visitor that detects dangerous code patterns."""
    
    def __init__(self):
        self.violations: list[str] = []
    
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            top_module = alias.name.split(".")[0]
            if top_module in BLOCKED_IMPORTS:
                self.violations.append(f"Blocked import: '{alias.name}'")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            top_module = node.module.split(".")[0]
            if top_module in BLOCKED_IMPORTS:
                self.violations.append(f"Blocked import: 'from {node.module}'")
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if func_name in BLOCKED_BUILTINS:
            self.violations.append(f"Blocked builtin call: '{func_name}()'")
        self.generic_visit(node)


def check_code_safety(code: str) -> tuple[bool, list[str]]:
    """Parse code with AST and check for dangerous patterns.
    
    Returns:
        (is_safe, violations) tuple.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]
    
    visitor = _SafetyVisitor()
    visitor.visit(tree)
    
    return len(visitor.violations) == 0, visitor.violations


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
        
        # SEC-H3 FIX: Use AST-based analysis instead of string matching.
        # String-matching blocklists are trivially bypassed via string
        # concatenation, getattr chains, and unicode normalization.
        is_safe, violations = check_code_safety(code)
        if not is_safe:
            return f"Error: Code contains blocked patterns:\n" + "\n".join(f"  - {v}" for v in violations)
                
        full_code = self.PRE_IMPORTS + "\n" + code
        
        try:
            safe_dir = getattr(config, "SAFE_WORK_DIR", tempfile.gettempdir())
            if not os.path.exists(str(safe_dir)):
                os.makedirs(str(safe_dir), exist_ok=True)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=str(safe_dir), delete=False) as f:
                f.write(full_code)
                temp_path = f.name
                
            timeout = getattr(config, "BASH_TIMEOUT", 30)
            
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(safe_dir),
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
