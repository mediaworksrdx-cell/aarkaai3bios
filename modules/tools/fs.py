"""
AARKAAI – File System Tools (Path-Sandboxed)

All file operations are restricted to SAFE_WORK_DIR.
Path traversal attacks (../../etc/passwd) are blocked.
"""
import os
from pathlib import Path
from typing import Any, Dict

from config import SAFE_WORK_DIR
from modules.tools.base import Tool


def _resolve_safe_path(path_str: str) -> Path:
    """
    Resolve a path ensuring it stays within SAFE_WORK_DIR.
    Raises ValueError if the path escapes the sandbox.
    """
    safe_dir = SAFE_WORK_DIR.resolve()
    safe_dir.mkdir(parents=True, exist_ok=True)

    # Resolve the full path (handles ../ etc.)
    if os.path.isabs(path_str):
        resolved = Path(path_str).resolve()
    else:
        resolved = (safe_dir / path_str).resolve()

    # Security check: must be within the sandbox
    try:
        resolved.relative_to(safe_dir)
    except ValueError:
        raise ValueError(
            f"Access denied: path '{path_str}' is outside the workspace. "
            f"All file operations must be within: {safe_dir}"
        )

    return resolved


class FileReadTool(Tool):
    name = "FileReadTool"
    description = (
        "Reads the contents of a file within the workspace. "
        "Provide 'path' argument (relative to workspace)."
    )

    def execute(self, params: Dict[str, Any]) -> str:
        path_str = params.get("path")
        if not path_str:
            return "Error: 'path' argument required."

        try:
            resolved = _resolve_safe_path(path_str)
        except ValueError as e:
            return f"Error: {e}"

        if not resolved.is_file():
            return f"Error: File '{path_str}' does not exist in workspace."

        try:
            content = resolved.read_text(encoding="utf-8")
            # Truncate very large files to avoid context window explosion
            if len(content) > 10000:
                content = content[:10000] + "\n...[truncated, file too large]"
            return content
        except Exception as exc:
            return f"Error reading file: {exc}"


class FileEditTool(Tool):
    name = "FileEditTool"
    description = (
        "Writes content to a file within the workspace. Overwrites by default. "
        "Provide 'path' and 'content'."
    )

    def execute(self, params: Dict[str, Any]) -> str:
        path_str = params.get("path")
        content = params.get("content")

        if not path_str or content is None:
            return "Error: 'path' and 'content' arguments are required."

        try:
            resolved = _resolve_safe_path(path_str)
        except ValueError as e:
            return f"Error: {e}"

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return f"Successfully wrote to {resolved.relative_to(SAFE_WORK_DIR.resolve())}"
        except Exception as exc:
            return f"Error writing file: {exc}"
