---
name: pdf
description: Document design and layout review standards. Use when designing, building, or reviewing PDF business reports, invoices, or publications.
---

# PDF Document Design & Quality Standards

When designing or reviewing PDF documents, you must evaluate the output across both presentation design and content depth:

## 1. Visual Design & Layout
* **Layout Grid:** Structured multi-column grid alignment, margins, and card padding.
* **Typography:** Professional font pairing, hierarchy, sizing (body text 11.5px to 12.5px, headings 16px to 22px), and legibility.
* **Color & Branding:** Harmonious, premium color palettes (e.g., custom HSL theme, sleek dark/light themes). Avoid default web primary colors.
* **Visualizations:** High-fidelity, clean matplotlib charts (custom colors, no top/right borders, clean grid lines, transparent backgrounds) embedded via Base64 data URLs.
* **Page Partitioning:** Explicit page breaks and containers (`.page { page-break-after: always; }`) to guarantee exactly 6 pages for business reports.

## 2. Content & Review
* **Depth:** High-density, professional paragraphs (minimum of 4-6 comprehensive sentences, totaling 300-400 words per page) to fully populate pages. No placeholders or empty gaps.
* **Relevance:** Ensure content is technically accurate, domain-correct, and tailored for executive presentation.
* **Dual Focus:** Never review only visual appearance. Always balance design aesthetics with deep, meaningful content.
