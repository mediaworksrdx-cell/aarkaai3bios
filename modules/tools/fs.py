"""
AARKAAI – File System Read & Edit Tools (Claude 2026 Edition)

Upgraded filesystem tools featuring:
- StartLine and EndLine windowed paginated reads for FileReadTool to prevent context bloat.
- AST compilation check validation before committing writes in FileEditTool.
"""
import os
import ast
import logging
from pathlib import Path
from typing import Any, Dict
from config import SAFE_WORK_DIR
from modules.tools.base import Tool

logger = logging.getLogger(__name__)

def _resolve_safe_path(path_str: str) -> Path:
    safe_dir = SAFE_WORK_DIR.resolve()
    safe_dir.mkdir(parents=True, exist_ok=True)

    if os.path.isabs(path_str):
        target = Path(path_str)
    else:
        target = Path(safe_dir / path_str)

    # Resolve symlinks and physical paths
    resolved = target.resolve()

    try:
        resolved.relative_to(safe_dir)
    except ValueError:
        raise ValueError(
            f"Access denied: path '{path_str}' is outside the workspace. "
            f"All file operations must be within: {safe_dir}"
        )

    # Explicitly block symbolic link operations to prevent traversal exploits
    if os.path.islink(target) or os.path.islink(resolved):
        raise ValueError("Access denied: Symbolic links are blocked for production safety.")

    return resolved

class FileReadTool(Tool):
    name = "FileReadTool"
    description = (
        "Reads file contents in the workspace. Supports window paging with optional "
        "'start_line' and 'end_line' (1-indexed, inclusive) parameters."
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 200

    def execute(self, params: Dict[str, Any]) -> str:
        path_str = params.get("path")
        if not path_str:
            return "Error: 'path' argument required."

        try:
            resolved = _resolve_safe_path(path_str)
        except ValueError as e:
            return f"Error: {e}"

        if not resolved.is_file():
            return f"Error: File '{path_str}' does not exist."

        ext = resolved.suffix.lower()
        if ext == ".pdf":
            try:
                import pdfplumber
                text_content = []
                with pdfplumber.open(resolved) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- PAGE {i+1} ---\n{page_text}")
                return "\n\n".join(text_content)
            except Exception as e:
                return f"Error parsing PDF: {e}"

        # Default text read
        try:
            lines = resolved.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            return f"Error reading file: {e}"

        start_line = params.get("start_line")
        end_line = params.get("end_line")

        if start_line is not None or end_line is not None:
            total_lines = len(lines)
            start = max(1, int(start_line)) if start_line is not None else 1
            end = min(total_lines, int(end_line)) if end_line is not None else total_lines
            
            sliced_lines = lines[start-1:end]
            header = f"--- [{path_str}] Lines {start} to {end} of {total_lines} ---\n"
            return header + "\n".join(sliced_lines)

        content = "\n".join(lines)
        if len(content) > 12000:
            content = content[:12000] + "\n...[truncated, file too large. Use start_line/end_line]"
        return content

class FileEditTool(Tool):
    name = "FileEditTool"
    description = "Writes new contents to a file. Performs AST compile syntax verification for python scripts."
    risk_level = "HIGH"
    latency_weight = 0.8
    cost_weight = 0.2
    base_confidence = 0.98

    permissions = ["read", "write"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 400

    def execute(self, params: Dict[str, Any]) -> str:
        path_str = params.get("path")
        content = params.get("content")

        if not path_str or content is None:
            return "Error: 'path' and 'content' arguments are required."

        # AST compile verification pass for Python modifications
        if path_str.endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError as syntax_err:
                return (
                    f"Write blocked: SyntaxError detected in python block script:\n"
                    f"Line {syntax_err.lineno}: {syntax_err.msg}\n"
                    f"Please correct the syntax before executing the write command."
                )

        try:
            resolved = _resolve_safe_path(path_str)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            
            # Atomic Write: write to temporary file first, then replace target file path
            temp_file = resolved.with_name(f".tmp_{resolved.name}")
            temp_file.write_text(content, encoding="utf-8")
            os.replace(temp_file, resolved)
            
            return f"Successfully wrote to {resolved.relative_to(SAFE_WORK_DIR.resolve())}"
        except Exception as e:
            # Clean up temp file if write fails
            if 'temp_file' in locals() and temp_file.exists():
                os.remove(temp_file)
            return f"Error writing file: {e}"
            return f"Error writing file: {e}"
