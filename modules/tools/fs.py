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

        # ── Intercept reportlab PDF attempts ─────────────────────────────────
        # The small LLM sometimes uses reportlab which produces empty/plain PDFs.
        # Force it to use the html skill + docs_generator.py instead.
        if path_str.endswith(".py") and "reportlab" in content:
            return (
                "Error: NEVER use reportlab to create PDFs — it produces plain, empty PDFs with no styling or content. "
                "You MUST use the html skill + docs_generator.py (weasyprint) instead. "
                "Your script must follow this exact pattern:\n\n"
                "import sys\n"
                "sys.path.insert(0, '/home/ubuntu/aarkaai3b')\n"
                "from skills.html.docs_generator import generate_pdf\n\n"
                "html_content = '''<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Title</title>"
                "<style>body{font-family:Arial,sans-serif;margin:40px;color:#222}"
                "h1{color:#1e3a8a;border-bottom:2px solid #3b82f6;padding-bottom:8px}"
                "h2{color:#1e40af;margin-top:28px}p{line-height:1.7}"
                "table{width:100%;border-collapse:collapse;margin:20px 0}"
                "th{background:#1e3a8a;color:white;padding:10px;text-align:left}"
                "td{padding:9px 10px;border-bottom:1px solid #e5e7eb}"
                "tr:nth-child(even) td{background:#f8fafc}"
                ".callout{background:#eff6ff;border-left:4px solid #3b82f6;padding:14px 18px;margin:16px 0}"
                "</style></head><body>"
                "<h1>YOUR TITLE HERE</h1>"
                "<p>REAL content paragraphs here...</p>"
                "<h2>Section</h2><p>More content...</p>"
                "<div class=\"callout\">Key insight here.</div>"
                "<table><tr><th>Col A</th><th>Col B</th></tr>"
                "<tr><td>Data</td><td>Data</td></tr></table>"
                "</body></html>'''\n\n"
                "generate_pdf(html_content, 'YOUR_OUTPUT.pdf')\n"
                "print('PDF generated successfully')\n\n"
                "Rewrite your script using docs_generator.py with REAL detailed HTML content about the user's topic."
            )

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

