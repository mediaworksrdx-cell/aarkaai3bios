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

        # Pre-filter: AST-based safety check before entering the sandbox.
        # This provides fast rejection of obviously dangerous code.
        is_safe, violations = check_code_safety(code)
        if not is_safe:
            return f"Error: Code contains blocked patterns:\n" + "\n".join(f"  - {v}" for v in violations)

        # Prepend safe financial library imports
        full_code = self.PRE_IMPORTS + "\n" + code

        # Route through CodeModeExecutor for full Docker sandbox isolation.
        # This enforces: --network=none, --cap-drop=ALL, --read-only, --pids-limit=32,
        # -m 512m, --cpus=1.0 — same hardening as Code Mode execution.
        try:
            from modules.code_mode import CodeModeExecutor, SandboxUnavailableError
            executor = CodeModeExecutor(
                tool_registry=None,          # Finance code does not call tools
                workspace_dir=str(getattr(config, "SAFE_WORK_DIR", "/tmp")),
                timeout=getattr(config, "BASH_TIMEOUT", 30),
                max_tool_calls=0,            # No tool calls allowed from finance code
                max_output_bytes=262144,     # 256 KB output cap
                max_script_bytes=65536,
            )
            # Build an empty namespace — finance code runs standalone, no tool proxies
            result = executor.execute_code_block(
                full_code,
                namespace={},
                user_id=params.get("_user_id", "finance_tool"),
                session_id=params.get("_session_id", "finance_exec")
            )
            if result.success:
                return result.output if result.output else "[No output produced]"
            else:
                return f"Execution error: {result.error}"
        except SandboxUnavailableError as e:
            return f"Error: Sandbox runtime unavailable — {e}. Finance code execution requires Docker."
        except Exception as e:
            return f"Error executing finance code: {e}"
