---
name: html
description: >
  Use this skill to convert raw text, CSV, JSON, code, invoices, or reports into
  beautiful, professional, self-contained HTML documents and render them to PDF.
---

# Universal Docs Generator Skill (Aarkaa)

## Purpose
Convert ANY input — code, research papers, invoices, business reports, meeting notes, product specs, raw text, JSON, CSV data — into a **beautiful, professional HTML document**, then render it to **PDF**.

## When to use
Trigger whenever the user asks to "create a doc", "generate a report/invoice/paper", "make this into a PDF", "turn this into a document", or uploads content asking for a polished output.

## Workflow
1. **Understand the content type**: code → technical doc with syntax-highlighted blocks; research paper → academic layout with abstract/sections/references; invoice → table-based billing layout; report/notes → executive summary + sections.
2. **Generate ONE self-contained HTML file** following the design system below.
3. **Call `docs_generator.py`** (or the HTML→PDF function) to render the HTML into a PDF.
4. **Deliver both** the .html and .pdf to the user.

## Design System (apply to every doc)
- **Structure**: `<header>` with title/subtitle/date/logo placeholder, `<main>` with sectioned content, `<footer>` with page info.
- **Typography**: Use system fonts ONLY — headings: `Arial, sans-serif` or `Georgia, serif`; body: `Arial, sans-serif`. DO NOT use `@import url('https://fonts.googleapis.com/...')` — this breaks PDF rendering on the server.
- **Color palette**: pick ONE accent color matching content tone (blue/teal = corporate, green = finance, purple = creative, dark navy = technical). Use it for headings, borders, table headers, callouts.
- **Layout**: max-width 900px content, generous padding (40-60px), 1.6 line-height.
- **Components to use as appropriate**:
  - Cover/title block with gradient or accent bar
  - Section headers with accent underline
  - Tables with alternating row colors and styled headers (for invoices, data, comparisons)
  - Callout/info boxes (colored left border + light background) for highlights/warnings
  - Code blocks: dark background, monospace font, syntax-colored if possible
  - Pull quotes for research papers
  - Footer with page numbers (`@page` CSS counters) for PDF
- **Print rules**: include `@media print` and `@page` CSS — set margins, page-break-inside: avoid on tables/cards, A4 size.

## Content-type templates

### Invoice
Header (company info + invoice #/date) → billed-to block → itemized table (description, qty, rate, amount) → totals box (subtotal/tax/total, right-aligned, highlighted) → payment terms footer.

### Research Paper
Title + authors block → abstract (italic, indented) → numbered sections (Introduction, Methods, Results, Discussion, References) → figures/tables with captions → references list.

### Code Documentation
Title + version → overview → installation/usage code blocks → API reference tables → examples with syntax highlighting.

### Business Report
Cover page → executive summary callout → sections with charts/tables → key metrics in card grid → recommendations/conclusion.

### Generic / Meeting Notes / Specs
Title + date/attendees → summary callout → structured sections with headers → action items as checklist-style list.

## Output requirements
- Single self-contained HTML file (CSS inline in `<head>`, NO external dependencies — no Google Fonts CDN, no CDN links)
- NEVER use `reportlab` — it produces empty PDFs with no content
- Always pass the generated HTML to `docs_generator.py` using this EXACT import:
  ```python
  import sys
  sys.path.insert(0, '/home/ubuntu/aarkaai3b')
  from skills.html.docs_generator import generate_pdf
  generate_pdf(html_content, 'output.pdf')
  ```
- Filenames: `generate_{topic}.py` for the script and `{topic}.pdf` for the output
