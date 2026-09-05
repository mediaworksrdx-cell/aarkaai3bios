#!/usr/bin/env python3
"""
Universal Docs Generator for Aarkaa
Converts a self-contained HTML string/file into a polished PDF.
Aarkaa's LLM generates the HTML (following SKILL.md design system);
this script handles the HTML -> PDF rendering step.

Usage:
    python docs_generator.py input.html output.pdf
    OR import and call generate_pdf(html_string, "output.pdf")

Requires: pip install weasyprint --break-system-packages
"""

import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Check for Weasyprint without crashing on missing C libraries (libgobject-2.0-0)
_WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML
    _WEASYPRINT_AVAILABLE = True
except (ImportError, OSError, Exception):
    _WEASYPRINT_AVAILABLE = False

def _find_browser_binary() -> str | None:
    """Find available headless browser (Edge, Chrome, Chromium, Brave)."""
    candidates = [
        shutil.which("msedge"),
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("brave"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


DEFAULT_PRINT_CSS = """
@page {
    size: A4;
    margin: 2cm;
}
@media print {
    table, .card, .callout { page-break-inside: avoid; }
    h1, h2, h3 { page-break-after: avoid; }
}
"""


def _sanitize_html(html_content: str) -> str:
    """
    Pre-process HTML before passing to weasyprint.
    Strips Google Fonts @import rules that cause KeyError in weasyprint 69.x
    when network access is unavailable or restricted.
    """
    import re
    # Remove @import url('https://fonts.googleapis.com/...') 
    # These cause KeyError: 'font-family' in weasyprint 69.x
    html_content = re.sub(
        r"@import\s+url\(['\"]?https?://fonts\.googleapis\.com[^)]*\)['\"]?\s*;?",
        "",
        html_content,
        flags=re.IGNORECASE
    )
    # Also remove <link> tags pointing to Google Fonts
    html_content = re.sub(
        r'<link[^>]+fonts\.googleapis\.com[^>]*>',
        "",
        html_content,
        flags=re.IGNORECASE
    )
    # Replace Google Fonts references in font-family with safe system fallbacks
    # e.g. font-family: 'Poppins', sans-serif -> font-family: Arial, sans-serif
    html_content = re.sub(
        r"font-family\s*:\s*['\"]?(Poppins|Playfair Display|Roboto|Outfit|Montserrat|Lato|Nunito|Raleway|Open Sans)['\"]?(\s*,\s*)?",
        "font-family: Arial, sans-serif;",
        html_content,
        flags=re.IGNORECASE
    )
    return html_content


def generate_pdf(html_content: str, output_path: str, inject_print_css: bool = True) -> str:
    """
    Render an HTML string to a PDF file using headless Edge/Chrome or WeasyPrint.
    """
    html_content = _sanitize_html(html_content)
    
    if inject_print_css:
        if "</head>" in html_content:
            html_content = html_content.replace(
                "</head>", f"<style>{DEFAULT_PRINT_CSS}</style></head>"
            )
        else:
            html_content = f"<style>{DEFAULT_PRINT_CSS}</style>" + html_content

    browser = _find_browser_binary()
    output_pdf = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    # 1. Prefer Headless Browser (Edge/Chrome) for perfect CSS/SVG/Canvas rendering
    if browser:
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
                tf.write(html_content)
                temp_html = tf.name

            cmd = [
                browser,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={output_pdf}",
                f"file:///{os.path.abspath(temp_html)}"
            ]
            res = subprocess.run(cmd, capture_output=True, timeout=45)
            try:
                os.remove(temp_html)
            except OSError:
                pass

            if res.returncode == 0 and os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
                return str(output_pdf)
        except Exception as browser_err:
            pass

    # 2. Fallback to WeasyPrint if available
    if _WEASYPRINT_AVAILABLE:
        try:
            HTML(string=html_content, base_url=None).write_pdf(output_pdf)
            return str(output_pdf)
        except Exception as wp_err:
            raise RuntimeError(f"Both browser and WeasyPrint PDF generation failed: {wp_err}")

    raise RuntimeError(
        "PDF generation requires Microsoft Edge, Google Chrome, or WeasyPrint. "
        "Neither a compatible browser binary nor WeasyPrint C-libraries were found."
    )


def generate_pdf_from_file(html_path: str, output_path: str, inject_print_css: bool = True) -> str:
    """Read an HTML file and render it to PDF."""
    html_content = Path(html_path).read_text(encoding="utf-8")
    return generate_pdf(html_content, output_path, inject_print_css)


def main():
    if len(sys.argv) != 3:
        print("Usage: python docs_generator.py <input.html> <output.pdf>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    if not Path(input_path).exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    result = generate_pdf_from_file(input_path, output_path)
    print(f"PDF generated: {result}")


if __name__ == "__main__":
    main()
