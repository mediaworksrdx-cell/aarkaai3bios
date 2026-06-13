---
name: premium-report
description: >
  Use this skill to generate high-end, multi-page business reports (6-10 pages) 
  which include an introduction/cover page, a watermark on the first page, 
  and detailed data/analytics sections with visualization charts on all subsequent pages.
---

# Premium Report Design & Generation Skill

This skill details how to compile a professional, multi-page business report PDF (6-10 pages) using WeasyPrint (HTML-to-PDF engine) and Python.

## Design Layout System

### 1. Document Structure & Page Allocation
* **Total Pages:** Enforce a strict page constraint of **6 to 10 pages**.
* **Page 1: Cover & Introduction:** Contains a clean corporate title, metadata block, and an executive abstract. **Must include a watermark overlay.**
* **Pages 2-10: Detailed Analytics:** Each subsequent page must focus on a dedicated topic/metric, containing detailed text, a structured data table, and a base64-embedded matplotlib chart.

### 2. Page Break Control (CSS)
Ensure that pages do not overflow randomly. Force each page boundaries explicitly:
```css
.page {
    height: 297mm; /* Standard A4 height */
    width: 210mm;  /* Standard A4 width */
    page-break-after: always;
    box-sizing: border-box;
}
.page:last-child {
    page-break-after: avoid;
}
```

### 3. First Page Watermark Implementation
To add a watermark **only on the first page** using pure CSS/HTML rendering:
```html
<div class="page" style="position: relative;">
    <!-- Centered Watermark overlay -->
    <div style="
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 64px;
        font-weight: bold;
        color: rgba(229, 231, 235, 0.4); /* Light grey with transparency */
        z-index: 0;
        pointer-events: none;
        white-space: nowrap;
    ">
        CONFIDENTIAL
    </div>
    
    <!-- Page 1 content here (ensure content is on top using z-index if needed) -->
</div>
```

---

## Technical Workflow & Code Template

Aarkaa agents must follow this Python template to generate premium reports.

```python
import sys
import os
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 1. Helper to generate charts dynamically
def get_chart_data(x_values, y_values, title):
    plt.figure(figsize=(6, 3), dpi=250)
    plt.plot(x_values, y_values, marker='o', color='#1e3a8a')
    plt.title(title, fontsize=10, fontweight='bold', color='#1e3a8a')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# 2. Render each chart base64
chart1 = get_chart_data([1,2,3], [10,20,15], "Financial Indicator 1")
chart2 = get_chart_data([1,2,3], [5,15,30], "Adoption Forecast 2")

# 3. Assemble Multi-Page HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 20mm;
    }}
    body {{
        font-family: Arial, sans-serif;
        color: #1f2937;
    }}
    .page {{
        page-break-after: always;
    }}
    .page:last-child {{
        page-break-after: avoid;
    }}
</style>
</head>
<body>

<!-- PAGE 1: Intro with Watermark -->
<div class="page" style="position: relative;">
    <div style="position: absolute; top:50%; left:50%; transform: translate(-50%, -50%) rotate(-45deg); font-size:60px; color:rgba(200,200,200,0.3); font-weight:bold; z-index:0;">
        CONFIDENTIAL
    </div>
    <div style="position: relative; z-index: 1;">
        <h1>Executive Business Report</h1>
        <p>Introduction details go here...</p>
    </div>
</div>

<!-- PAGE 2: Details & Chart 1 -->
<div class="page">
    <h2>Financial Analysis</h2>
    <p>Detailed explanations...</p>
    <img src="data:image/png;base64,{{chart1}}" />
</div>

<!-- PAGE 3: Details & Chart 2 -->
<div class="page">
    <h2>Market Forecast</h2>
    <p>Detailed forecast text...</p>
    <img src="data:image/png;base64,{{chart2}}" />
</div>

<!-- Repeat up to 6-10 pages -->

</body>
</html>
"""

# 4. Generate the PDF
sys.path.insert(0, '/home/ubuntu/aarkaai3b')
from skills.html.docs_generator import generate_pdf
generate_pdf(html_content, 'premium_report.pdf')
print('Premium PDF generated successfully.')
```
