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
        "Supports PDF, DOCX, XLSX, XLS, CSV, JSON, and text formats automatically. "
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

        ext = resolved.suffix.lower()

        # Handle PDF
        if ext == ".pdf":
            try:
                import pdfplumber
                text_content = []
                with pdfplumber.open(resolved) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- PAGE {i+1} ---\n{page_text}")
                content = "\n\n".join(text_content)
                if not content.strip():
                    return "File exists but no readable text layer found (it might be a scanned image PDF)."
            except Exception as exc:
                return f"Error parsing PDF: {exc}"

        # Handle Word Document (DOCX)
        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(resolved)
                content = "\n".join([p.text for p in doc.paragraphs])
            except Exception as exc:
                return f"Error parsing DOCX: {exc}"

        # Handle Excel (XLSX, XLS)
        elif ext in [".xlsx", ".xls"]:
            try:
                import pandas as pd
                xl = pd.ExcelFile(resolved)
                sheets_content = []
                for sheet_name in xl.sheet_names:
                    df = xl.parse(sheet_name)
                    sheets_content.append(f"--- SHEET: {sheet_name} ---\n{df.to_string()}")
                content = "\n\n".join(sheets_content)
            except Exception as exc:
                return f"Error parsing Excel file: {exc}"

        # Default text/csv/json fallback
        else:
            try:
                content = resolved.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = resolved.read_text(encoding="latin-1")
                except Exception as exc:
                    return f"Error reading binary file as text: {exc}"
            except Exception as exc:
                return f"Error reading file: {exc}"

        # Truncate very large outputs to avoid context window explosion
        if len(content) > 12000:
            content = content[:12000] + "\n...[truncated, file too large]"
        return content


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

        # ── Fail-safe for previous message PDF generation placeholders ──────
        if (".py" in path_str.lower() or "previous" in path_str.lower() or "report" in path_str.lower()) and "generate_pdf" in content:
            prev_msg_path = SAFE_WORK_DIR / "previous_message.txt"
            if prev_msg_path.is_file():
                try:
                    actual_text = prev_msg_path.read_text(encoding="utf-8").strip()
                    actual_words = [w.lower() for w in actual_text.split() if len(w) > 4]
                    sample_words = actual_words[:10]
                    has_actual_content = any(w in content.lower() for w in sample_words) if sample_words else True
                    
                    if actual_text and (not has_actual_content or any(p in content for p in ["The previous message...", "Data analysis and insights", "Executive Summary details", "actual content", "placeholder"])):
                        lines = actual_text.split("\n")
                        formatted_html_body = []
                        current_page_content = []
                        page_count = 1
                        
                        def wrap_page(items, page_num):
                            watermark = ""
                            if page_num == 1:
                                watermark = '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-45deg);font-size:60px;color:rgba(200,200,200,0.1);font-weight:bold;pointer-events:none;z-index:999;">CONFIDENTIAL</div>'
                            return f'<div class="page" style="position:relative;">{watermark}\n' + "\n".join(items) + '\n</div>'

                        for line in lines:
                            line_strip = line.strip()
                            if not line_strip:
                                continue
                            if line_strip.startswith("###"):
                                if current_page_content:
                                    formatted_html_body.append(wrap_page(current_page_content, page_count))
                                    current_page_content = []
                                    page_count += 1
                                current_page_content.append(f"<h3>{line_strip.lstrip('#').strip()}</h3>")
                            elif line_strip.startswith("##"):
                                if current_page_content:
                                    formatted_html_body.append(wrap_page(current_page_content, page_count))
                                    current_page_content = []
                                    page_count += 1
                                current_page_content.append(f"<h2>{line_strip.lstrip('#').strip()}</h2>")
                            elif line_strip.startswith("#"):
                                if current_page_content:
                                    formatted_html_body.append(wrap_page(current_page_content, page_count))
                                    current_page_content = []
                                    page_count += 1
                                current_page_content.append(f"<h1>{line_strip.lstrip('#').strip()}</h1>")
                            elif line_strip.startswith("-") or line_strip.startswith("*"):
                                current_page_content.append(f"<li>{line_strip.lstrip('-*').strip()}</li>")
                            else:
                                current_page_content.append(f"<p>{line_strip}</p>")
                        
                        if current_page_content:
                            formatted_html_body.append(wrap_page(current_page_content, page_count))
                            
                        html_pages = "\n\n<!-- PAGE BREAK -->\n\n".join(formatted_html_body)
                        title = "Previous Message Report"
                        if "elon musk" in actual_text.lower():
                            title = "Elon Musk Biography"
                        
                        premium_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
@page {{
    size: A4;
    margin: 20mm;
}}
body {{
    font-family: Arial, sans-serif;
    font-size: 12px;
    line-height: 1.6;
    color: #333;
}}
.page {{
    page-break-after: always;
    position: relative;
    min-height: 240mm;
}}
.page:last-child {{
    page-break-after: avoid;
}}
h1 {{
    color: #1e3a8a;
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 8px;
    margin-top: 0;
}}
h2 {{
    color: #1e40af;
    margin-top: 24px;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
}}
h3 {{
    color: #1d4ed8;
}}
p {{
    text-align: justify;
    margin-bottom: 12px;
}}
li {{
    margin-bottom: 6px;
}}
</style>
</head>
<body>
{html_pages}
</body>
</html>"""
                        escaped_html = premium_html.replace('\\', '\\\\').replace("'''", "\\'\\'\\'").replace('"""', '\\"\\"\\"')
                        import re
                        pattern = r'(html_content\s*=\s*)([\'"]{3})(.*?)([\'"]{3})'
                        new_content, count = re.subn(pattern, f"html_content = '''{escaped_html}'''", content, flags=re.DOTALL)
                        if count > 0:
                            content = new_content
                except Exception as e:
                    logger.error("Error in previous_message fail-safe: %s", e)

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

