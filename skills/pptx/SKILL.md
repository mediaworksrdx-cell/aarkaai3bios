---
name: pptx
description: >
  Use this skill for anything involving PowerPoint presentations (.pptx) —
  creating slide decks, reading/extracting content from presentations, editing
  slides, adding charts, images, tables, or formatting. Trigger whenever the
  user mentions slides, a deck, presentation, or .pptx file.
---

# PPTX Skill

Use **python-pptx** for all PowerPoint tasks.

## Installation
```bash
pip install python-pptx pillow
```

---

## 1. Creating a Presentation

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()

# Slide dimensions (default 16:9)
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)
```

---

## 2. Adding Slides

```python
# Use a blank layout
blank_layout = prs.slide_layouts[6]   # 6 = blank
title_layout = prs.slide_layouts[0]   # 0 = title slide
content_layout = prs.slide_layouts[1] # 1 = title + content

slide = prs.slides.add_slide(blank_layout)
```

---

## 3. Adding Text Boxes

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

txBox = slide.shapes.add_textbox(
    Inches(1), Inches(1),   # left, top
    Inches(8), Inches(2)    # width, height
)
tf = txBox.text_frame
tf.word_wrap = True

p = tf.paragraphs[0]
p.text = "Slide Title"
p.font.bold = True
p.font.size = Pt(36)
p.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
```

---

## 4. Title + Content Slide

```python
slide = prs.slides.add_slide(content_layout)

title = slide.shapes.title
title.text = "Section Title"

body = slide.placeholders[1]
tf = body.text_frame

tf.text = "First bullet"
tf.add_paragraph().text = "Second bullet"
tf.add_paragraph().text = "Third bullet"

for para in tf.paragraphs:
    para.font.size = Pt(20)
```

---

## 5. Background Color

```python
from pptx.oxml.ns import qn
from lxml import etree

def set_slide_background(slide, hex_color: str):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(hex_color)

set_slide_background(slide, "1F497D")  # dark blue
```

---

## 6. Adding Images

```python
slide.shapes.add_picture(
    "image.png",
    left=Inches(1), top=Inches(2),
    width=Inches(5)   # height auto-scales
)
```

---

## 7. Adding a Table

```python
from pptx.util import Inches

rows, cols = 4, 3
table = slide.shapes.add_table(
    rows, cols,
    Inches(1), Inches(2),
    Inches(8), Inches(3)
).table

headers = ["Product", "Q1", "Q2"]
for col_idx, header in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.text = header
    cell.text_frame.paragraphs[0].font.bold = True

data = [("Widget A", "$10k", "$14k"), ("Widget B", "$8k", "$11k"), ("Widget C", "$6k", "$9k")]
for row_idx, row in enumerate(data, 1):
    for col_idx, val in enumerate(row):
        table.cell(row_idx, col_idx).text = val
```

---

## 8. Adding a Chart

```python
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

chart_data = ChartData()
chart_data.categories = ["Q1", "Q2", "Q3", "Q4"]
chart_data.add_series("Revenue", (10, 14, 12, 18))

chart = slide.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED,
    Inches(2), Inches(2),
    Inches(6), Inches(4),
    chart_data
).chart

chart.has_title = True
chart.chart_title.text_frame.text = "Quarterly Revenue"
```

---

## 9. Reading an Existing Presentation

```python
prs = Presentation("existing.pptx")

for slide_num, slide in enumerate(prs.slides, 1):
    print(f"\n--- Slide {slide_num} ---")
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                print(para.text)
```

---

## 10. Saving

```python
prs.save("output.pptx")
```

---

## Common Slide Layouts (index → name)

| Index | Layout |
|---|---|
| 0 | Title Slide |
| 1 | Title and Content |
| 2 | Title and Two Content |
| 5 | Title Only |
| 6 | Blank |
