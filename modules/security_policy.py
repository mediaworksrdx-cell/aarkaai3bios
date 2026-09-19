"""
AARKAAI - Centralized Security Policy (FIX-11)

Single source of truth for all security rules:
  - Forbidden Python import sets (AST-based)
  - Forbidden builtin/attribute sets (AST-based)
  - Bash always-blocked patterns (compiled regex)
  - Bash allowed command allowlist
  - Git allowed/blocked subcommand sets
  - Shared AST validation functions

All security-enforcing modules (bash.py, code_mode.py, execution_engine.py,
finance_code_tool.py, permissions.py) MUST import from here rather than
maintaining independent, potentially divergent sets.
"""
from __future__ import annotations

import ast
import re
import logging
from typing import FrozenSet

logger = logging.getLogger(__name__)

# === Python AST: Forbidden imports ============================================
FORBIDDEN_IMPORTS: FrozenSet[str] = frozenset({
    "os", "sys", "subprocess", "pty", "ptyprocess", "signal",
    "shutil", "pathlib", "glob", "tempfile",
    "socket", "ssl", "http", "urllib", "requests", "aiohttp", "httpx",
    "ftplib", "smtplib", "telnetlib", "xmlrpc", "imaplib",
    "pickle", "shelve", "marshal", "dill", "cloudpickle",
    "ctypes", "cffi",
    "importlib", "importlib_metadata", "pkgutil", "compileall", "code", "codeop",
    "paramiko", "fabric",
})

FORBIDDEN_IMPORTS_EXCEPTIONS: FrozenSet[str] = frozenset()

# === Python AST: Forbidden builtins ===========================================
FORBIDDEN_BUILTINS: FrozenSet[str] = frozenset({
    "exec", "eval", "compile", "__import__", "open",
    "breakpoint", "exit", "quit",
    "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "hasattr",
    "memoryview", "bytearray",
})

# === Python AST: Forbidden attributes =========================================
FORBIDDEN_ATTRIBUTES: FrozenSet[str] = frozenset({
    "__class__", "__subclasses__", "__builtins__", "__import__",
    "__reduce__", "__reduce_ex__", "__getattribute__",
    "__init_subclass__", "__bases__", "__mro__",
    "system", "popen", "spawn", "execv", "execve", "execvp",
    "fork", "forkpty", "dup2", "fdopen",
    "rmtree", "remove", "unlink", "rename", "replace",
})

# === Bash: Always-blocked patterns (compiled) =================================
_BASH_BLOCKED_PATTERNS_RAW = [
    r'\|\s*(?:bash|sh|zsh|dash|csh|ksh)\b',
    r'[`]',
    r'\$\(',
    r'\beval\b',
    r'\bexec\b',
    r'\bsudo\b',
    r'\bsu\b\s',
    r'\brm\s+(-[rRf]+\s+)?/',
    r'\brm\s+-[rRf]*\s',
    r'\bchmod\b.*\b777\b',
    r'\bchown\b',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r'>\s*/dev/',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bpoweroff\b',
    r'\bsystemctl\b',
    r'\bkill\b\s+-9',
    r'\bkillall\b',
    r'\bnc\b.*-[le]',
    r'\btelnet\b',
    r'\bssh\b',
    r'\bscp\b',
    r':\(\)\{',
    r'/etc/(?:passwd|shadow|sudoers)',
    r'\bwget\b.*-O\s*-\s*\|',
    r'\bcurl\b.*\|\s*(?:bash|sh)',
    r'\b(?:pip|pip3)(?:\.\d+)?\b',
]

BASH_ALWAYS_BLOCKED: list = [
    re.compile(p, re.IGNORECASE) for p in _BASH_BLOCKED_PATTERNS_RAW
]

# === Bash: Permitted base commands ============================================
BASH_ALLOWED_COMMANDS: FrozenSet[str] = frozenset({
    "node", "npm", "npx",
    "cat", "head", "tail", "wc", "grep", "find", "ls", "pwd", "echo",
    "sort", "uniq", "tr", "cut", "awk", "sed",
    "file", "stat", "du", "df", "tree",
    "git", "diff",
    "curl", "wget",
    "python", "python3", "pytest", "ruff", "mypy", "black", "flake8", "isort",
    "make", "cmake",
    "mkdir", "touch", "cp", "mv",
})

# === Git: Permitted and blocked subcommands ===================================
GIT_ALLOWED_SUBCOMMANDS: FrozenSet[str] = frozenset({
    "status", "diff", "log", "branch", "show", "fetch",
    "clone", "checkout", "add", "commit", "stash", "tag",
    "remote", "pull", "config",
})

GIT_BLOCKED_SUBCOMMANDS: FrozenSet[str] = frozenset({
    "push", "reset", "clean", "gc", "reflog",
    "filter-branch", "filter-repo", "bisect",
    "worktree", "submodule",
})


# === AST Validation Functions =================================================

def validate_python_ast(code: str) -> tuple[bool, str]:
    """
    Parse code with Python AST and reject forbidden imports, builtins, attributes.

    Returns:
        (is_valid, reason) - reason is empty string on success.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base in FORBIDDEN_IMPORTS and base not in FORBIDDEN_IMPORTS_EXCEPTIONS:
                    return False, f"Forbidden import: '{alias.name}'"

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base = node.module.split(".")[0]
                if base in FORBIDDEN_IMPORTS and base not in FORBIDDEN_IMPORTS_EXCEPTIONS:
                    return False, f"Forbidden import: 'from {node.module}'"

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_BUILTINS:
                    return False, f"Forbidden builtin call: '{node.func.id}()'"

        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRIBUTES:
                return False, f"Forbidden attribute access: '.{node.attr}'"

    return True, ""


def validate_bash_command(command: str) -> tuple[bool, str]:
    """
    Validate a bash command string against BASH_ALWAYS_BLOCKED patterns.

    Returns:
        (is_valid, reason) - reason is empty string on success.
    """
    if not command or not command.strip():
        return False, "Empty command"

    for compiled_pattern in BASH_ALWAYS_BLOCKED:
        if compiled_pattern.search(command):
            return False, f"Command matches blocked pattern: {compiled_pattern.pattern!r}"

    return True, ""
