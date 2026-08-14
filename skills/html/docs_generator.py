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
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    print("ERROR: weasyprint not installed. Run:")
    print("  pip install weasyprint --break-system-packages")
    sys.exit(1)


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
    Render an HTML string to a PDF file.

    Args:
        html_content: Full HTML document as a string (self-contained, inline CSS).
        output_path: Path to write the resulting PDF.
        inject_print_css: If True, appends sensible @page/print rules
                           (A4, page-break controls) before rendering.

    Returns:
        The output_path on success.
    """
    # Strip network-dependent CSS that causes errors in weasyprint 69.x
    html_content = _sanitize_html(html_content)
    
    if inject_print_css:
        if "</head>" in html_content:
            html_content = html_content.replace(
                "</head>", f"<style>{DEFAULT_PRINT_CSS}</style></head>"
            )
        else:
            html_content = f"<style>{DEFAULT_PRINT_CSS}</style>" + html_content

    HTML(string=html_content, base_url=None).write_pdf(output_path)
    return output_path


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
