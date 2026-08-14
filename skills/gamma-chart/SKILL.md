---
name: gamma-chart
description: >
  Generate premium, high-DPI matplotlib or fallback vector SVG charts with custom styles
  matching Gamma's modern aesthetics, supporting both base64 embedding and separate file exports.
---

# Gamma-Style Premium Chart Generation System

This skill defines the technical and aesthetic standards for creating beautiful, transparent-background data visualizations for premium business reports. It includes robust systems for falling back from `matplotlib` to inline vector `SVG` and exporting charts as separate disk assets when embedding fails or memory limits are exceeded.

---

## 1. Aesthetic Guidelines (Modern Visual Style)
* **Backgrounds:** Always transparent (`facecolor='none'`).
* **Gridlines:** Soft, thin dashed gridlines (`#E2E8F0` or `#CBD5E1`) with low opacity (`0.5`).
* **Borders:** Hide top and right spines/borders to keep the layout modern and light.
* **Colors:** Use a curated theme:
  - Primary: `#6366F1` (Indigo) / `#4F46E5` (Deep Indigo)
  - Secondary: `#10B981` (Emerald) or `#F59E0B` (Amber) or `#8B5CF6` (Purple)
* **Labels & Typography:** Bold headings, clear contrasting data labels on bars, and small slate-colored labels.

---

## 2. Technical Implementation with Matplotlib
Always use the non-interactive `Agg` backend:
```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
```

### Standard Plot Compilation:
```python
fig, ax = plt.subplots(figsize=(6.5, 3.0), dpi=300, facecolor='none')
ax.set_facecolor('none')
# ... plot elements ...
plt.tight_layout()
plt.savefig(buf_or_path, format='png', bbox_inches='tight', transparent=True)
plt.close()
```

---

## 3. Robust Dual Fallback Mechanisms
To ensure 100% successful document compilation, follow this hierarchy:
1. **Primary:** Matplotlib chart generation (rendered as PNG and encoded to base64 or written to a separate file).
2. **Secondary (Matplotlib Missing/Fails):** Compile a clean vector `SVG` string using Python's string formatting and encode to a base64 Data URL.
3. **Tertiary (Embedding Limits):** Write the generated PNG or SVG to a **separate file** on the local disk (e.g., `chart1.png`) and reference it in the HTML using an absolute `file:///` path.

### Absolute File Path Referencing:
```html
<img src="file:///workspace/aarkaai3b/safe_dir/charts/chart1.png" class="chart-img">
```
This is highly recommended for WeasyPrint as it eliminates large inline base64 string parsing overhead and ensures perfect rendering.
