---
name: gamma-pdf
description: >
  Compile premium, A4, exactly 6-page PDF business reports inspired by Gamma.
  Features custom CSS grid layouts, running header/footer margin boxes, and card components.
---

# Gamma-Style Premium PDF Document Design & Compilation System

This skill outlines the strict A4 layout design guidelines, CSS token system, and print styling rules required to compile gorgeous, professional, multi-page business intelligence reports using WeasyPrint.

---

## 1. Page Setup & Margins (Strict 6 Pages)
To maintain an exact 6-page count without overflow, we wrap pages in separate containers and define page layout rules:

```css
@page {
    size: A4;
    margin: 24mm 16mm 20mm 16mm;
    
    @top-left {
        content: "AARKAA INTELLIGENCE";
        font-family: system-ui, sans-serif;
        font-size: 8px;
        font-weight: 700;
        color: #94A3B8;
        letter-spacing: 1.5px;
    }
    @top-right {
        content: "CONFIDENTIAL BUSINESS REPORT";
        font-family: system-ui, sans-serif;
        font-size: 8px;
        font-weight: 700;
        color: #EF4444;
        letter-spacing: 1.5px;
    }
    @bottom-left {
        content: "Prepared by Aarka AI";
        font-family: system-ui, sans-serif;
        font-size: 8px;
        color: #94A3B8;
    }
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-family: system-ui, sans-serif;
        font-size: 8px;
        font-weight: 600;
        color: #94A3B8;
    }
}

/* Cover page overrides */
@page:first {
    margin: 0;
    @top-left { content: ""; }
    @top-right { content: ""; }
    @bottom-left { content: ""; }
    @bottom-right { content: ""; }
}
```

### Explicit Page Boundaries:
Every page must be wrapped in a `.page` container:
```css
.page {
    height: 255mm;
    page-break-after: always;
    position: relative;
}
.page:last-child {
    page-break-after: avoid;
}
```

---

## 2. Layout Components & Grid Systems
* **Grid Row & Columns:**
  ```css
  .row { display: flex; gap: 16px; margin-bottom: 12px; }
  .col { flex: 1; }
  .col-4 { flex: 0 0 33.333%; }
  .col-8 { flex: 0 0 66.666%; }
  ```
* **Gamma Card (`.card`):**
  ```css
  .card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-top: 4px solid #6366F1;
      border-radius: 8px;
      padding: 18px 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }
  ```
* **Premium Callout (`.callout`):**
  ```css
  .callout {
      background: #F5F3FF;
      border-left: 4px solid #6366F1;
      padding: 14px 18px;
      border-radius: 0 8px 8px 0;
      font-style: italic;
      color: #4F46E5;
  }
  ```
* **Pill Badges (`.badge`):**
  ```css
  .badge {
      display: inline-block;
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #4F46E5;
      background: #EEF2F6;
      padding: 4px 10px;
      border-radius: 9999px;
  }
  ```

---

## 3. High-Density Text & Content Formatting
Ensure each page contains at least 300-400 words of rich, professional analysis. Placeholders or empty pages are not allowed. Text must be structured with beautiful hierarchy: headings (`h1` for document title, `h2` for section title), justified paragraph tags (`p`), and bulleted lists where appropriate.
