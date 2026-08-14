"""
tools.py — Step 1: The Tools

These are the actions your LLM agent can take.
Each function does one thing and returns a plain string result.
The LLM reads that result and decides what to do next.
"""

import os
import subprocess
import json
from pathlib import Path


# ─── Safety: restrict to a working directory ─────────────────────────────────

WORKSPACE = Path(os.environ.get("AGENT_WORKSPACE", "./workspace")).resolve()

def _safe_path(path: str) -> Path:
    """Resolve path and ensure it stays inside WORKSPACE."""
    resolved = (WORKSPACE / path).resolve()
    if not str(resolved).startswith(str(WORKSPACE)):
        raise PermissionError(f"Access outside workspace is not allowed: {path}")
    return resolved


# ─── Tool 1: Read a file ──────────────────────────────────────────────────────

def read_file(path: str) -> str:
    """
    Read the contents of a file.
    Returns the file content as a string, or an error message.
    """
    try:
        full_path = _safe_path(path)
        if not full_path.exists():
            return f"Error: file not found: {path}"
        if not full_path.is_file():
            return f"Error: not a file: {path}"
        return full_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"


# ─── Tool 2: Write a file ─────────────────────────────────────────────────────

def write_file(path: str, content: str) -> str:
    """
    Write content to a file. Creates directories if needed.
    Overwrites if file already exists.
    Returns a success or error message.
    """
    try:
        full_path = _safe_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"✓ Written {len(content)} chars to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


# ─── Tool 3: List files ───────────────────────────────────────────────────────

def list_files(directory: str = ".") -> str:
    """
    List files and folders in a directory (2 levels deep).
    Returns a formatted tree string.
    """
    try:
        root = _safe_path(directory)
        if not root.exists():
            return f"Error: directory not found: {directory}"

        lines = [f"📁 {directory}/"]
        for item in sorted(root.rglob("*")):
            # Skip hidden files and __pycache__
            parts = item.relative_to(root).parts
            if any(p.startswith(".") or p == "__pycache__" for p in parts):
                continue
            depth = len(parts)
            if depth > 2:
                continue
            indent = "  " * depth
            icon = "📄" if item.is_file() else "📁"
            lines.append(f"{indent}{icon} {item.name}")

        return "\n".join(lines) if len(lines) > 1 else f"(empty directory)"
    except Exception as e:
        return f"Error listing files: {e}"


# ─── Tool 4: Run a shell command ──────────────────────────────────────────────

def run_command(command: str, timeout: int = 30) -> str:
    """
    Run a shell command inside the workspace directory.
    Returns stdout + stderr combined, truncated to 3000 chars.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        return output[:3000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error running command: {e}"


# ─── Tool 5: Search code ──────────────────────────────────────────────────────

def search_code(query: str, file_pattern: str = "*") -> str:
    """
    Search for a text pattern across files in the workspace.
    Returns matching lines with file names and line numbers.
    """
    try:
        matches = []
        for file_path in WORKSPACE.rglob(file_pattern):
            if not file_path.is_file():
                continue
            parts = file_path.relative_to(WORKSPACE).parts
            if any(p.startswith(".") or p == "__pycache__" for p in parts):
                continue
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
                for i, line in enumerate(lines, 1):
                    if query.lower() in line.lower():
                        rel = file_path.relative_to(WORKSPACE)
                        matches.append(f"{rel}:{i}:  {line.strip()}")
            except Exception:
                continue

        if not matches:
            return f"No matches found for '{query}'"
        return "\n".join(matches[:50])  # cap at 50 results
    except Exception as e:
        return f"Error searching: {e}"


# ─── Tool registry ────────────────────────────────────────────────────────────
# This is what gets passed to your LLM's tool/function calling API.

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to the file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates it if it doesn't exist, overwrites if it does.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "Relative path to the file"},
                "content": {"type": "string", "description": "Full content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List files and folders in a directory (2 levels deep).",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory to list (default: workspace root)"}
            },
            "required": []
        }
    },
    {
        "name": "run_command",
        "description": "Run a shell command in the workspace. Use for installing packages, running tests, executing scripts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "search_code",
        "description": "Search for a text/code pattern across all files in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":        {"type": "string", "description": "Text to search for"},
                "file_pattern": {"type": "string", "description": "Glob pattern to filter files, e.g. '*.py'"}
            },
            "required": ["query"]
        }
    }
]


# ─── Tool dispatcher ──────────────────────────────────────────────────────────
# Call this when the LLM returns a tool_use block.

def execute_tool(name: str, args: dict) -> str:
    """Route a tool call from the LLM to the right function."""
    tools = {
        "read_file":   lambda a: read_file(a["path"]),
        "write_file":  lambda a: write_file(a["path"], a["content"]),
        "list_files":  lambda a: list_files(a.get("directory", ".")),
        "run_command": lambda a: run_command(a["command"], a.get("timeout", 30)),
        "search_code": lambda a: search_code(a["query"], a.get("file_pattern", "*")),
    }
    if name not in tools:
        return f"Unknown tool: {name}"
    return tools[name](args)
