---
name: premium-report
description: >
  Use this skill to generate high-end, multi-page business reports (exactly 6 pages)
  which include an elegant cover page, running headers/footers, and a visual card-based
  layout inspired by Gamma's premium, modern design aesthetic.
---

# Gamma-Style Premium PDF Document Design System

This skill outlines the styling, layout guidelines, and technical templates for generating premium, high-density, multi-page business reports (exactly 6 pages) using WeasyPrint. The design is inspired by modern web presentations like Gamma, featuring clean card grids, curated color palettes, elegant typography, and transparent data visualizations.

---

## 1. Core Design Guidelines (The Gamma Aesthetic)

### A. Curated Color Palette
Avoid browser default colors. Use this modern, premium theme:
* **Primary (Accent):** `#6366F1` (Indigo) / `#4F46E5` (Deep Indigo)
* **Secondary:** `#10B981` (Emerald) or `#F59E0B` (Amber)
* **Dark Neutral (Text):** `#1E293B` (Slate-800)
* **Light Neutral (Background):** `#F8FAFC` (Slate-50)
* **Card Background:** `#FFFFFF` (White)
* **Card Border/Dividers:** `#E2E8F0` (Slate-200)

### B. Modern Typography
Use a clean, modern system font stack that renders beautifully on all operating systems:
```css
font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
```
* **Headings:** Bold, dark slate (`#0F172A`), with slight letter-spacing adjustments.
* **Body Text:** Slate-800 (`#1E293B`), line-height of `1.6` for optimal readability.

### C. Cards, Badges, & Callouts (The Layout Blocks)
* **Gamma Cards (`.card`):** Wrap key content blocks in white cards with soft borders, top accent lines, and subtle shadows.
  ```css
  .card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-top: 4px solid #6366F1; /* Primary accent */
      border-radius: 8px;
      padding: 18px 24px;
      margin-bottom: 20px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
      page-break-inside: avoid;
  }
  ```
* **Pill Badges (`.badge`):** Small status indicators or section markers:
  ```css
  .badge {
      display: inline-block;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #4F46E5;
      background: #EEF2F6;
      padding: 4px 10px;
      border-radius: 9999px;
      margin-bottom: 8px;
  }
  ```
* **Premium Callouts (`.callout`):** Highlight boxes for key takeaways or warnings:
  ```css
  .callout {
      background: #F5F3FF; /* Very soft purple */
      border-left: 4px solid #6366F1;
      padding: 14px 18px;
      border-radius: 0 8px 8px 0;
      margin: 16px 0;
      font-style: italic;
      color: #4F46E5;
  }
  ```

---

## 2. Page Setup & Document Architecture (Strict 6 Pages)

To ensure a perfect multi-page layout without arbitrary overflows or blank pages, adhere to these rules:

### A. WeasyPrint Page Rules & Margin Boxes
Use CSS `@page` to define margins and premium running headers and footers:
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

/* Hide header/footer on the cover page */
@page:first {
    margin: 0;
    @top-left { content: ""; }
    @top-right { content: ""; }
    @bottom-left { content: ""; }
    @bottom-right { content: ""; }
}
```

### B. Strict Page Sizing
Wrap each page in a `<div class="page">` container with explicit page-break rules:
```css
.page {
    height: 255mm; /* Dynamic height for content inside margins */
    page-break-after: always;
    box-sizing: border-box;
    position: relative;
}
.page:last-child {
    page-break-after: avoid;
}
```

---

## 3. High-Quality Matplotlib Chart Styling
To make charts fit beautifully into the Gamma cards, style them with a matching transparent/clean theme:
```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def get_gamma_chart(x, y, title, chart_type='line', color='#6366F1'):
    # Create figure with transparent background and high DPI
    fig, ax = plt.subplots(figsize=(6, 2.8), dpi=300, facecolor='none')
    ax.set_facecolor('none')
    
    if chart_type == 'bar':
        bars = ax.bar(x, y, color=color, alpha=0.85, width=0.6, edgecolor='none')
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=7, fontweight='bold', color='#1E293B')
    else:
        ax.plot(x, y, marker='o', color=color, linewidth=2.5, markersize=5, markerfacecolor='#FFFFFF', markeredgewidth=2)
        ax.fill_between(x, y, color=color, alpha=0.1)  # Premium area fill
        
    # Title & Typography
    ax.set_title(title.upper(), fontsize=9, fontweight='bold', color='#0F172A', pad=12, letter_spacing=1)
    ax.tick_params(colors='#64748B', labelsize=7)
    
    # Elegant gridlines & borders
    ax.grid(True, linestyle='--', color='#E2E8F0', alpha=0.6, linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    
    plt.tight_layout()
    
    # Encode as Base64
    from io import BytesIO
    import base64
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')
```

---

## 4. Complete Python PDF Generation Script Pattern

Use this template as your structural blueprint:

```python
import sys
import os
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

# 1. Chart helper functions defined here...
def get_gamma_chart(x, y, title, chart_type='line', color='#6366F1'):
    # (Implementation as shown in Section 3)
    ...

# 2. Pre-generate all 5 distinct charts
chart1 = get_gamma_chart(['Q1', 'Q2', 'Q3', 'Q4'], [150, 220, 310, 480], "Quarterly Revenue Growth", "line", "#6366F1")
chart2 = get_gamma_chart(['SaaS', 'Fintech', 'Health', 'AI'], [42, 28, 19, 64], "Sector Distribution (%)", "bar", "#10B981")
# (Generate chart3, chart4, chart5...)

# 3. Assemble the HTML Structure
html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    /* Reset and Typography */
    * {{ box-sizing: border-box; }}
    body {{
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
        color: #1E293B;
        background-color: #F8FAFC;
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }}
    
    /* Page Layout & Breaks */
    @page {{
        size: A4;
        margin: 24mm 16mm 20mm 16mm;
        @top-left {{
            content: "AARKAA INTELLIGENCE";
            font-family: system-ui, sans-serif;
            font-size: 8px;
            font-weight: 700;
            color: #94A3B8;
            letter-spacing: 1.5px;
        }}
        @top-right {{
            content: "CONFIDENTIAL BUSINESS REPORT";
            font-family: system-ui, sans-serif;
            font-size: 8px;
            font-weight: 700;
            color: #EF4444;
            letter-spacing: 1.5px;
        }}
        @bottom-left {{
            content: "Prepared by Aarka AI";
            font-family: system-ui, sans-serif;
            font-size: 8px;
            color: #94A3B8;
        }}
        @bottom-right {{
            content: "Page " counter(page) " of " counter(pages);
            font-family: system-ui, sans-serif;
            font-size: 8px;
            font-weight: 600;
            color: #94A3B8;
        }}
    }}
    @page:first {{
        margin: 0;
        @top-left {{ content: ""; }}
        @top-right {{ content: ""; }}
        @bottom-left {{ content: ""; }}
        @bottom-right {{ content: ""; }}
    }}
    
    .page {{
        height: 255mm;
        page-break-after: always;
        position: relative;
    }}
    .page:last-child {{
        page-break-after: avoid;
    }}
    
    /* Layout Elements */
    .card {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 4px solid #6366F1;
        border-radius: 8px;
        padding: 18px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .card-green {{ border-top-color: #10B981; }}
    .card-amber {{ border-top-color: #F59E0B; }}
    
    .badge {{
        display: inline-block;
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #4F46E5;
        background: #EEF2F6;
        padding: 4px 10px;
        border-radius: 9999px;
        margin-bottom: 8px;
    }}
    .callout {{
        background: #F5F3FF;
        border-left: 4px solid #6366F1;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin: 16px 0;
        font-style: italic;
        color: #4F46E5;
    }}
    
    /* Typography Utilities */
    h1, h2, h3 {{ color: #0F172A; margin-top: 0; }}
    h1 {{ font-size: 26px; font-weight: 800; }}
    h2 {{ font-size: 18px; font-weight: 700; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 16px; }}
    p {{ font-size: 11.5px; line-height: 1.6; margin-bottom: 12px; }}
    
    /* Flex/Grid Helper (Weasyprint supports Flexbox) */
    .row {{ display: flex; gap: 16px; margin-bottom: 16px; }}
    .col {{ flex: 1; }}
    .col-4 {{ flex: 0 0 33.333%; }}
    .col-8 {{ flex: 0 0 66.666%; }}
    
    /* Tables */
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 10.5px; }}
    th {{ background: #0F172A; color: #ffffff; font-weight: 600; padding: 8px 10px; text-align: left; }}
    td {{ padding: 8px 10px; border-bottom: 1px solid #E2E8F0; }}
    tr:nth-child(even) td {{ background: #F8FAFC; }}
    
    /* Charts */
    .chart-container {{ text-align: center; margin: 12px 0; }}
    .chart-img {{ width: 100%; max-height: 250px; object-fit: contain; }}
</style>
</head>
<body>

<!-- PAGE 1: COVER PAGE -->
<div class="page" style="background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%); margin: 0; height: 297mm; display: flex; flex-direction: column; justify-content: space-between; padding: 40mm 20mm 20mm 20mm; color: #FFFFFF;">
    <!-- Sleek Subtle Watermark backdrop -->
    <div style="position: absolute; top: 35%; left: 5%; font-size: 90px; font-weight: 900; color: rgba(255,255,255,0.03); letter-spacing: 4px; pointer-events: none; z-index: 0;">
        INTELLIGENCE
    </div>
    
    <div style="z-index: 1;">
        <div style="width: 60px; height: 6px; background: #6366F1; margin-bottom: 24px; border-radius: 3px;"></div>
        <h1 style="color: #FFFFFF; font-size: 42px; line-height: 1.1; font-weight: 900; margin-bottom: 16px; letter-spacing: -1px;">
            Strategic Market Opportunity Report
        </h1>
        <p style="color: #94A3B8; font-size: 14px; max-width: 500px; line-height: 1.6; font-weight: 400;">
            A high-density qualitative and quantitative analysis outlining emergent sector trends, adoption curves, and growth methodologies prepared dynamically.
        </p>
    </div>
    
    <div style="z-index: 1; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 24px; display: flex; justify-content: space-between; font-size: 10px; color: #94A3B8;">
        <div>
            <strong style="color: #FFFFFF; display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px;">PREPARED BY</strong>
            Aarka Intelligence Platform
        </div>
        <div>
            <strong style="color: #FFFFFF; display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px;">DATE</strong>
            June 2026
        </div>
        <div>
            <strong style="color: #FFFFFF; display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px;">DOCUMENT CLASSIFICATION</strong>
            Highly Confidential
        </div>
    </div>
</div>

<!-- PAGE 2: EXECUTIVE SUMMARY & INCEPTION -->
<div class="page">
    <div class="badge">Inception</div>
    <h2>Executive Summary</h2>
    <div class="row">
        <div class="col-8">
            <div class="card">
                <p><strong>Core Thesis:</strong> This section outlines the structural dynamics of the subject area, detailing key microeconomic drivers and core catalysts triggering market shifts. High-density, professional paragraphs here provide deep insights into the long-term strategic landscape.</p>
                <p>We analyze the market's response to emergent variables, examining both regulatory headwinds and capital allocation trends. These elements combine to define the foundational baseline of our 6-page strategic evaluation.</p>
            </div>
            <div class="callout">
                "Strategic agility coupled with data-driven modeling is the defining differentiator in high-velocity markets."
            </div>
        </div>
        <div class="col-4">
            <div class="card card-amber">
                <strong style="font-size: 11px; color: #0F172A; display: block; margin-bottom: 8px;">KEY INSIGHTS</strong>
                <ul style="margin: 0; padding-left: 14px; font-size: 10px; line-height: 1.6;">
                    <li style="margin-bottom: 6px;">Capital migration towards highly scalable, AI-integrated platforms.</li>
                    <li style="margin-bottom: 6px;">Traditional market boundaries dissolving under cloud consolidation.</li>
                    <li>Regulatory compliance emerging as a core competitive moat.</li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="card card-green">
        <div class="row" style="align-items: center; margin-bottom: 0;">
            <div class="col-6">
                <p style="margin-bottom: 0;">The visual chart to the right captures the initial adoption velocity across core demographics, demonstrating the compounding growth curve of the platform.</p>
            </div>
            <div class="col-6 chart-container">
                <img class="chart-img" src="data:image/png;base64,{chart1}">
            </div>
        </div>
    </div>
</div>

<!-- PAGES 3, 4, 5, 6 continue here with card layouts, high-density text, and charts -->
...

</body>
</html>
"""

# 4. Compile the PDF
sys.path.insert(0, '/home/ubuntu/aarkaai3b')
from skills.html.docs_generator import generate_pdf
generate_pdf(html_content, 'market_report.pdf')
print('Gamma-style Premium PDF generated successfully.')
```
